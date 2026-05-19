"""
Monitoring and metrics service
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import json
import time

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collect and track application metrics"""
    
    def __init__(self):
        """Initialize metrics collector"""
        self.metrics = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'errors': 0,
            'last_updated': None
        })
        self.query_history = []
        self.error_history = []
        self.token_usage = {
            'total_tokens': 0,
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'embedding_tokens': 0
        }
    
    def record_query(
        self,
        endpoint: str,
        duration: float,
        success: bool = True,
        tokens_used: int = 0,
        error: Optional[str] = None
    ):
        """
        Record a query metric
        
        Args:
            endpoint: API endpoint
            duration: Query duration in seconds
            success: Whether query was successful
            tokens_used: Number of tokens used
            error: Error message if failed
        """
        metric = self.metrics[endpoint]
        metric['count'] += 1
        metric['total_time'] += duration
        metric['last_updated'] = datetime.utcnow().isoformat()
        
        if not success:
            metric['errors'] += 1
        
        # Record in history
        self.query_history.append({
            'endpoint': endpoint,
            'timestamp': datetime.utcnow().isoformat(),
            'duration': duration,
            'success': success,
            'tokens_used': tokens_used,
            'error': error
        })
        
        # Keep only last 1000 queries
        if len(self.query_history) > 1000:
            self.query_history = self.query_history[-1000:]
        
        # Track token usage
        if tokens_used > 0:
            self.token_usage['total_tokens'] += tokens_used
        
        # Record errors
        if error:
            self.error_history.append({
                'endpoint': endpoint,
                'timestamp': datetime.utcnow().isoformat(),
                'error': error
            })
            
            # Keep only last 100 errors
            if len(self.error_history) > 100:
                self.error_history = self.error_history[-100:]
        
        logger.info(f"Metric recorded: {endpoint} - {duration:.2f}s - Success: {success}")
    
    def record_tokens(
        self,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        embedding_tokens: int = 0
    ):
        """Record token usage"""
        self.token_usage['prompt_tokens'] += prompt_tokens
        self.token_usage['completion_tokens'] += completion_tokens
        self.token_usage['embedding_tokens'] += embedding_tokens
        self.token_usage['total_tokens'] += (prompt_tokens + completion_tokens + embedding_tokens)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        return {
            'endpoints': dict(self.metrics),
            'token_usage': self.token_usage,
            'total_queries': len(self.query_history),
            'total_errors': len(self.error_history),
            'recent_queries': self.query_history[-10:],
            'recent_errors': self.error_history[-10:]
        }
    
    def get_endpoint_stats(self, endpoint: str) -> Dict[str, Any]:
        """Get statistics for a specific endpoint"""
        metric = self.metrics.get(endpoint, {})
        
        if metric.get('count', 0) == 0:
            return {
                'endpoint': endpoint,
                'count': 0,
                'avg_duration': 0,
                'error_rate': 0
            }
        
        return {
            'endpoint': endpoint,
            'count': metric['count'],
            'avg_duration': metric['total_time'] / metric['count'],
            'total_time': metric['total_time'],
            'errors': metric['errors'],
            'error_rate': metric['errors'] / metric['count'],
            'last_updated': metric['last_updated']
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        total_queries = sum(m['count'] for m in self.metrics.values())
        total_errors = sum(m['errors'] for m in self.metrics.values())
        total_time = sum(m['total_time'] for m in self.metrics.values())
        
        return {
            'total_queries': total_queries,
            'total_errors': total_errors,
            'error_rate': total_errors / total_queries if total_queries > 0 else 0,
            'avg_response_time': total_time / total_queries if total_queries > 0 else 0,
            'token_usage': self.token_usage,
            'endpoints': len(self.metrics),
            'uptime': 'N/A'  # Would need start time tracking
        }
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics.clear()
        self.query_history.clear()
        self.error_history.clear()
        self.token_usage = {
            'total_tokens': 0,
            'prompt_tokens': 0,
            'completion_tokens': 0,
            'embedding_tokens': 0
        }
        logger.info("Metrics reset")


class PerformanceMonitor:
    """Monitor performance of operations"""
    
    def __init__(self, operation_name: str, metrics_collector: Optional[MetricsCollector] = None):
        """
        Initialize performance monitor
        
        Args:
            operation_name: Name of the operation to monitor
            metrics_collector: Optional metrics collector
        """
        self.operation_name = operation_name
        self.metrics_collector = metrics_collector
        self.start_time = None
        self.end_time = None
        self.duration = None
        self.success = True
        self.error = None
    
    def __enter__(self):
        """Start monitoring"""
        self.start_time = time.time()
        logger.debug(f"Starting operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End monitoring"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        
        if exc_type is not None:
            self.success = False
            self.error = str(exc_val)
            logger.error(f"Operation failed: {self.operation_name} - {self.error}")
        else:
            logger.info(f"Operation completed: {self.operation_name} - {self.duration:.2f}s")
        
        # Record in metrics collector if provided
        if self.metrics_collector:
            self.metrics_collector.record_query(
                endpoint=self.operation_name,
                duration=self.duration,
                success=self.success,
                error=self.error
            )
        
        return False  # Don't suppress exceptions


class StructuredLogger:
    """Structured logging with JSON format"""
    
    def __init__(self, name: str):
        """Initialize structured logger"""
        self.logger = logging.getLogger(name)
    
    def log(
        self,
        level: str,
        message: str,
        **kwargs
    ):
        """
        Log structured message
        
        Args:
            level: Log level (info, warning, error, debug)
            message: Log message
            **kwargs: Additional structured data
        """
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level.upper(),
            'message': message,
            **kwargs
        }
        
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(json.dumps(log_data))
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.log('info', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.log('warning', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.log('error', message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.log('debug', message, **kwargs)


# Global metrics collector instance
metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector"""
    return metrics_collector

# Made with Bob
