import asyncio
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import URLError
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.engine.external_fetcher import LiveWeatherFetcher
from app.engine.knn_checker import SpatialKNNChecker
from app.engine.lstm_model import LSTMEngine
from app.engine.repair_engine import SelfHealingPipeline
from app.engine.rule_checker import RuleChecker
from app.models.observation import Observation

router = APIRouter(prefix="/api/v1")

_BACKEND_DIR = Path(__file__).resolve().parents[2]
weather_fetcher = LiveWeatherFetcher()
rule_checker = RuleChecker()
spatial_checker = SpatialKNNChecker(max_distance_km=50.0)
repair_pipeline = SelfHealingPipeline()
lstm_engine = LSTMEngine(
    model_path=_BACKEND_DIR / "models_store" / "lstm_v1.onnx",
    scaler_path=_BACKEND_DIR / "models_store" / "scaler.pkl",
)


@router.get("/health")
async def api_health_check() -> dict[str, object]:
    return {
        "status": "online",
        "onnx_lstm_ready": lstm_engine.ready,
        "database": "connected",
    }


class RepairObservationRequest(BaseModel):
    station_id: str = Field(min_length=1)
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    temperature: float = Field(allow_inf_nan=False)
    pressure: float = Field(allow_inf_nan=False)
    humidity: float = Field(allow_inf_nan=False)


def _surrounding_coordinates(
    center_lat: float,
    center_lon: float,
    count: int,
    radius_km: float = 40.0,
) -> list[dict[str, Any]]:
    coordinates = [
        {
            "station_id": "AWS_CENTER_0",
            "name": "Central AWS Node",
            "lat": center_lat,
            "lon": center_lon,
        }
    ]
    longitude_scale = max(abs(math.cos(math.radians(center_lat))), 1e-6)

    for index in range(1, count):
        angle = (2 * math.pi / (count - 1)) * (index - 1)
        delta_lat = (radius_km / 111.0) * math.cos(angle)
        delta_lon = (radius_km / (111.0 * longitude_scale)) * math.sin(angle)
        coordinates.append(
            {
                "station_id": f"AWS_DYNAMIC_{index:02d}",
                "name": f"Surrounding Node {index}",
                "lat": round(center_lat + delta_lat, 4),
                "lon": round(center_lon + delta_lon, 4),
            }
        )

    return coordinates


async def _fetch_weather(node: dict[str, Any]) -> dict[str, Any]:
    return await asyncio.to_thread(
        weather_fetcher.fetch_live_station_data,
        node["lat"],
        node["lon"],
        node["station_id"],
    )


async def _fetch_weather_for_nodes(
    nodes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    try:
        return list(await asyncio.gather(*(_fetch_weather(node) for node in nodes)))
    except (URLError, ValueError, OSError) as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Open-Meteo did not return valid station data: {exc}",
        ) from exc


async def _recent_history(
    station_id: str,
    db: AsyncSession,
) -> list[Observation]:
    result = await db.execute(
        select(Observation)
        .where(Observation.station_id == station_id)
        .order_by(Observation.timestamp.desc())
        .limit(12)
    )
    return list(reversed(result.scalars().all()))


async def _process_observation(
    raw_reading: dict[str, Any],
    neighbor_readings: list[dict[str, Any]],
    db: AsyncSession,
) -> dict[str, Any]:
    history = await _recent_history(raw_reading["station_id"], db)
    recent_history = [
        {
            "temperature": item.temperature,
            "pressure": item.pressure,
            "humidity": item.humidity,
        }
        for item in history
    ]

    qc_flag, reason = rule_checker.check_reading(raw_reading, recent_history)
    spatial_average = None
    if neighbor_readings:
        spatial_anomaly, spatial_reason, spatial_average = (
            spatial_checker.evaluate_spatial_consistency(
                raw_reading,
                neighbor_readings,
            )
        )
        if spatial_anomaly:
            qc_flag, reason = "FAULTY", spatial_reason

    is_anomaly = qc_flag != "GOOD"
    lstm_prediction = None
    if is_anomaly and lstm_engine.ready and len(history) == 12:
        sequence = [
            [item.temperature, item.pressure, item.humidity]
            for item in history
        ]
        try:
            lstm_prediction = await asyncio.to_thread(
                lstm_engine.predict_next,
                sequence,
            )
        except RuntimeError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"LSTM inference failed: {exc}",
            ) from exc

    repaired = repair_pipeline.repair_observation(
        raw_reading,
        is_anomaly,
        reason,
        lstm_predicted=lstm_prediction,
        spatial_avg_temp=spatial_average,
    )

    db.add(
        Observation(
            id=str(uuid4()),
            station_id=raw_reading["station_id"],
            temperature=repaired["temperature"],
            pressure=repaired["pressure"],
            humidity=repaired["humidity"],
            qc_flag=qc_flag,
            flag_reason=reason,
        )
    )

    return {
        **raw_reading,
        "raw_temperature": raw_reading["temperature"],
        "temperature": repaired["temperature"],
        "repaired_temperature": repaired["temperature"],
        "pressure": repaired["pressure"],
        "humidity": repaired["humidity"],
        "has_anomaly": is_anomaly,
        "qc_flag": qc_flag,
        "flag_reason": reason,
        "repair_method": repaired["repair_method"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/live-surrounding-stations")
async def get_live_surrounding_stations(
    lat: float = Query(17.3850, ge=-90.0, le=90.0),
    lon: float = Query(78.4866, ge=-180.0, le=180.0),
    count: int = Query(6, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
) -> dict[str, list[dict[str, Any]]]:
    nodes = _surrounding_coordinates(lat, lon, count)
    live_readings = await _fetch_weather_for_nodes(nodes)

    for reading in live_readings:
        reading["name"] = next(
            node["name"] for node in nodes
            if node["station_id"] == reading["station_id"]
        )

    stations = []
    for reading in live_readings:
        neighbors = [
            item for item in live_readings
            if item["station_id"] != reading["station_id"]
        ]
        stations.append(await _process_observation(reading, neighbors, db))

    await db.commit()
    return {"stations": stations}


@router.post("/anomalies/repair")
async def repair_anomaly(
    request: RepairObservationRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    nodes = _surrounding_coordinates(
        request.latitude,
        request.longitude,
        count=6,
    )[1:]
    neighbors = await _fetch_weather_for_nodes(nodes)
    reading = request.model_dump()

    repaired = await _process_observation(reading, neighbors, db)
    await db.commit()
    return {"observation": repaired}
