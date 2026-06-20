from __future__ import annotations

import random
from datetime import datetime

from fastapi import APIRouter

router = APIRouter(tags=["dashboard"])


def random_accuracy() -> str:
    return f"{random.uniform(96.5, 99.9):.1f}%"


def random_alert_count() -> int:
    return random.randint(5, 12)


def random_blocked_sources() -> int:
    return random.randint(3, 8)


def random_status() -> str:
    return random.choice(["Operational", "Monitoring", "Alert Mode"])


def random_severity() -> str:
    return random.choice(["Low", "Medium", "High"])


def random_attack_type() -> str:
    return random.choice(["DoS Attack", "Probe", "Malware", "R2L", "U2R", "Normal Traffic"])


def current_timestamp() -> str:
    return datetime.now().strftime("%d-%b-%Y %I:%M:%S %p")


@router.get("/api/dashboard/overview")
def dashboard_overview() -> dict[str, object]:
    return {
        "main_output_dashboard": {
            "network_traffic_monitoring": "Active flow monitoring with recent packet counts",
            "live_detection_status": "Monitoring suspicious activities in real time",
            "security_status": random_status(),
            "intrusion_statistics": {
                "alerts_last_24h": random_alert_count(),
                "blocked_sources": random_blocked_sources(),
                "detection_accuracy": random_accuracy(),
            },
            "last_updated": current_timestamp(),
        },
        "detection_output": [
            {
                "source_ip": "192.168.1.10",
                "destination_ip": "10.0.0.5",
                "attack_type": random_attack_type(),
                "severity": random_severity(),
                "status": random.choice(["Detected", "Safe"]),
            },
            {
                "source_ip": "192.168.1.15",
                "destination_ip": "10.0.0.8",
                "attack_type": random_attack_type(),
                "severity": random_severity(),
                "status": random.choice(["Detected", "Safe"]),
            },
        ],
        "alert_output": {
            "message": "⚠ ALERT GENERATED",
            "threat_type": random.choice(["DDoS Attack", "Probe", "Malware"]),
            "source_ip": random.choice(["192.168.1.10", "172.16.0.15", "10.1.1.202"]),
            "severity": random.choice(["Medium", "High"]),
            "detection_time": current_timestamp(),
            "recommended_action": "Block source IP and investigate network logs.",
        },
        "machine_learning_output": {
            "prediction_result": random.choice(["Intrusion Detected", "Normal Traffic"]),
            "attack_category": [
                "DoS",
                "Probe",
                "R2L",
                "U2R",
                "Malware",
                "Normal Traffic",
            ],
            "confidence_score": f"{random.uniform(80.0, 99.9):.1f}%",
        },
        "reports": {
            "daily_security_report": "Complete",
            "weekly_threat_analysis": "Complete",
            "attack_trend_graphs": {
                "trend": random.choice(["increasing", "stable", "decreasing"]),
                "top_attack_type": random.choice(["DoS", "Probe", "Malware"]),
            },
            "top_malicious_ips": [
                "192.168.1.10",
                "10.1.1.202",
                "172.16.0.15",
            ],
            "false_positive_rate": f"{random.uniform(1.5, 3.5):.1f}%",
            "false_negative_rate": f"{random.uniform(0.5, 2.0):.1f}%",
            "overall_accuracy": random_accuracy(),
        },
    }


def random_alert() -> dict[str, object]:
    return {
        "threat_type": random.choice(["DDoS Attack", "Probe", "Malware"]),
        "source_ip": random.choice(["192.168.1.10", "172.16.0.15", "10.1.1.202"]),
        "severity": random.choice(["Medium", "High"]),
        "detection_time": current_timestamp(),
        "recommended_action": "Block source IP and investigate network logs.",
    }


@router.get("/api/alerts/latest")
def get_latest_alert() -> dict[str, object]:
    return random_alert()


@router.get("/api/reports/summary")
def get_report_summary() -> dict[str, object]:
    return {
        "daily_security_report": random.choice(["Complete", "Updated", "Pending"]),
        "weekly_threat_analysis": random.choice(["Complete", "Updated", "Pending"]),
        "attack_trend_graphs": {
            "trend": random.choice(["increasing", "stable", "decreasing"]),
            "top_attack_type": random.choice(["DoS", "Probe", "Malware"]),
        },
        "top_malicious_ips": [
            "192.168.1.10",
            "10.1.1.202",
            "172.16.0.15",
        ],
        "false_positive_rate": f"{random.uniform(1.0, 4.0):.1f}%",
        "false_negative_rate": f"{random.uniform(0.5, 2.5):.1f}%",
        "overall_accuracy": f"{random.uniform(95.0, 99.9):.1f}%",
    }
