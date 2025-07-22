import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import threading


class MetricsCollector:
    """Simple metrics collector for tracking application performance"""
    
    def __init__(self):
        self._metrics: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._start_time = time.time()
    
    def increment_counter(self, name: str, value: int = 1, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        with self._lock:
            key = self._get_metric_key(name, tags)
            if key not in self._metrics:
                self._metrics[key] = {"type": "counter", "value": 0, "tags": tags or {}}
            self._metrics[key]["value"] += value
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a histogram metric (for timing, sizes, etc.)"""
        with self._lock:
            key = self._get_metric_key(name, tags)
            if key not in self._metrics:
                self._metrics[key] = {
                    "type": "histogram", 
                    "values": [], 
                    "tags": tags or {},
                    "count": 0,
                    "sum": 0.0,
                    "min": float('inf'),
                    "max": float('-inf')
                }
            
            metric = self._metrics[key]
            metric["values"].append(value)
            metric["count"] += 1
            metric["sum"] += value
            metric["min"] = min(metric["min"], value)
            metric["max"] = max(metric["max"], value)
            
            # Keep only last 1000 values to prevent memory issues
            if len(metric["values"]) > 1000:
                metric["values"] = metric["values"][-1000:]
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric (current state)"""
        with self._lock:
            key = self._get_metric_key(name, tags)
            self._metrics[key] = {
                "type": "gauge", 
                "value": value, 
                "tags": tags or {},
                "timestamp": time.time()
            }
    
    def record_timing(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None):
        """Record timing information"""
        self.record_histogram(f"{name}_duration_ms", duration * 1000, tags)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics"""
        with self._lock:
            metrics_snapshot = {}
            for key, metric in self._metrics.items():
                if metric["type"] == "histogram":
                    values = metric["values"]
                    if values:
                        avg = metric["sum"] / metric["count"]
                        values_sorted = sorted(values)
                        p50 = values_sorted[len(values_sorted) // 2]
                        p95 = values_sorted[int(len(values_sorted) * 0.95)]
                        p99 = values_sorted[int(len(values_sorted) * 0.99)]
                        
                        metrics_snapshot[key] = {
                            "type": metric["type"],
                            "count": metric["count"],
                            "sum": metric["sum"],
                            "avg": avg,
                            "min": metric["min"],
                            "max": metric["max"],
                            "p50": p50,
                            "p95": p95,
                            "p99": p99,
                            "tags": metric["tags"]
                        }
                else:
                    metrics_snapshot[key] = metric.copy()
            
            # Add system metrics
            metrics_snapshot["system_uptime_seconds"] = {
                "type": "gauge",
                "value": time.time() - self._start_time,
                "tags": {}
            }
            
            return metrics_snapshot
    
    def reset_metrics(self):
        """Reset all metrics"""
        with self._lock:
            self._metrics.clear()
    
    def _get_metric_key(self, name: str, tags: Optional[Dict[str, str]]) -> str:
        """Generate a unique key for the metric"""
        if not tags:
            return name
        
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}|{tag_str}"


# Global metrics instance
metrics = MetricsCollector()


class TimingContext:
    """Context manager for timing operations"""
    
    def __init__(self, metrics_collector: MetricsCollector, name: str, tags: Optional[Dict[str, str]] = None):
        self.metrics = metrics_collector
        self.name = name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.metrics.record_timing(self.name, duration, self.tags)
            
            # Also track success/failure
            status = "error" if exc_type else "success"
            tags_with_status = (self.tags or {}).copy()
            tags_with_status["status"] = status
            self.metrics.increment_counter(f"{self.name}_total", 1, tags_with_status)


def time_operation(name: str, tags: Optional[Dict[str, str]] = None):
    """Decorator for timing function calls"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with TimingContext(metrics, name, tags):
                return func(*args, **kwargs)
        return wrapper
    return decorator
