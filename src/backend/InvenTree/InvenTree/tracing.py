"""OpenTelemetry setup functions."""

import base64
import logging
from typing import Optional

from opentelemetry import metrics, trace
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor
from opentelemetry.instrumentation.system_metrics import SystemMetricsInstrumentor
from opentelemetry.sdk import _logs as logs
from opentelemetry.sdk import resources
from opentelemetry.sdk._logs import export as logs_export
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    ConsoleMetricExporter,
    PeriodicExportingMetricReader,
)
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

import InvenTree.ready
from InvenTree.version import inventreeVersion

TRACE_PROC = None
TRACE_PROV = None


def setup_tracing(
    endpoint: str,
    headers: dict,
    resources_input: Optional[dict] = None,
    console: bool = False,
    auth: Optional[dict] = None,
    is_http: bool = False,
    append_http: bool = True,
):  # pragma: no cover
    """Set up tracing for the application in the current context.

    Args:
        endpoint: The endpoint to send the traces to.
        headers: The headers to send with the traces.
        resources_input: The resources to send with the traces.
        console: Whether to output the traces to the console.
        auth: Dict with auth information
        is_http: Whether to use HTTP or gRPC for the exporter.
        append_http: Whether to append '/v1/traces' to the endpoint.
    """
    if InvenTree.ready.isImportingData() or InvenTree.ready.isRunningMigrations():
        return

    # Logger configuration
    logger = logging.getLogger('inventree')

    if resources_input is None:
        resources_input = {}
    if auth is None:
        auth = {}

    # Setup the auth headers
    if 'basic' in auth:
        basic_auth = auth['basic']
        if 'username' in basic_auth and 'password' in basic_auth:
            auth_raw = f'{basic_auth["username"]}:{basic_auth["password"]}'
            auth_token = base64.b64encode(auth_raw.encode('utf-8')).decode('utf-8')
            headers['Authorization'] = f'Basic {auth_token}'
        else:
            logger.warning('Basic auth is missing username or password')

    # Clean up headers
    headers = {k: v for k, v in headers.items() if v is not None}

    # Initialize the OTLP Resource
    service_name = 'Unknown'
    if InvenTree.ready.isInServerThread():
        service_name = 'BACKEND'
    elif InvenTree.ready.isInWorkerThread():
        service_name = 'WORKER'
    resource = resources.Resource(
        attributes={
            resources.SERVICE_NAME: service_name,
            resources.SERVICE_NAMESPACE: 'INVENTREE',
            resources.SERVICE_VERSION: inventreeVersion(),
            **resources_input,
        }
    )

    # Import the OTLP exporters
    if is_http:
        from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
    else:
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )

    # Spans / Traces
    span_exporter = OTLPSpanExporter(
        headers=headers,
        endpoint=endpoint if not (is_http and append_http) else f'{endpoint}/v1/traces',
    )
    trace_processor = BatchSpanProcessor(span_exporter)
    trace_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(trace_provider)
    trace_provider.add_span_processor(trace_processor)
    # For debugging purposes, export the traces to the console
    if console:
        trace_provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    # Metrics
    metric_periodic_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(
            headers=headers,
            endpoint=endpoint
            if not (is_http and append_http)
            else f'{endpoint}/v1/metrics',
        )
    )
    metric_readers = [metric_periodic_reader]

    # For debugging purposes, export the metrics to the console
    if console:
        console_metric_exporter = ConsoleMetricExporter()
        console_metric_reader = PeriodicExportingMetricReader(console_metric_exporter)
        metric_readers.append(console_metric_reader)

    meter_provider = MeterProvider(resource=resource, metric_readers=metric_readers)
    metrics.set_meter_provider(meter_provider)

    # Logs
    log_exporter = OTLPLogExporter(
        headers=headers,
        endpoint=endpoint if not (is_http and append_http) else f'{endpoint}/v1/logs',
    )
    log_provider = logs.LoggerProvider(resource=resource)
    log_provider.add_log_record_processor(
        logs_export.BatchLogRecordProcessor(log_exporter)
    )
    handler = logs.LoggingHandler(level=logging.INFO, logger_provider=log_provider)
    logger = logging.getLogger('inventree')
    logger.addHandler(handler)

    global TRACE_PROC, TRACE_PROV
    TRACE_PROC = trace_processor
    TRACE_PROV = trace_provider


def setup_instruments(db_engine: str):  # pragma: no cover
    """Run auto-instrumentation for OpenTelemetry tracing."""
    DjangoInstrumentor().instrument()
    RedisInstrumentor().instrument()
    RequestsInstrumentor().instrument()
    SystemMetricsInstrumentor().instrument()

    db_engine = str(db_engine).lower().strip()

    # DBs
    if 'sqlite' in db_engine:
        SQLite3Instrumentor().instrument()
    elif 'postgresql' in db_engine:
        try:
            from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor

            PsycopgInstrumentor().instrument(
                enable_commenter=False, commenter_options={}
            )
        except ModuleNotFoundError:
            pass
    elif 'mysql' in db_engine:
        try:
            from opentelemetry.instrumentation.pymysql import PyMySQLInstrumentor

            PyMySQLInstrumentor().instrument()
        except ModuleNotFoundError:
            pass
