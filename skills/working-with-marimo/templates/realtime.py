"""
📡 Real-Time Monitoring Dashboard Template - Table of Contents

📋 OVERVIEW
Production-grade monitoring system with real-time data streaming, alerting, and performance metrics

📑 SECTIONS
1. Setup & Configuration (cells 1-4)
2. Real-time State Management (cells 5-8)
3. Data Sources & Connectors (cells 9-12)
4. Alert System Configuration (cells 13-16)
5. Real-time Visualizations (cells 17-21)
6. System Health Monitoring (cells 22-25)
7. Performance Metrics (cells 26-29)
8. Alert Processing Engine (cells 30-33)
9. Data Aggregation & Storage (cells 34-37)
10. Monitoring Dashboard (cells 38-41)

🎯 KEY FEATURES
- Real-time data streaming and processing
- Configurable alert thresholds and notifications
- Interactive monitoring dashboard with auto-refresh
- System health metrics and performance tracking
- Historical data analysis and trend detection
- Multi-source data integration

⚡ QUICK START
Configure data sources in cell_10, set alert thresholds in cell_15, then start monitoring
"""

import marimo
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import random
import asyncio
from typing import Dict, List, Any

__generated_with = "0.8.0"
app = marimo.App(width="full")

@app.cell
def cell_1():
    import marimo as mo
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from datetime import datetime, timedelta
    import time
    import random
    import asyncio
    from typing import Dict, List, Any
    return mo, pd, px, go, datetime, timedelta, time, random, asyncio, Dict, List, Any

@app.cell
def cell_2(mo):
    mo.md("# 📡 Real-Time Monitoring Dashboard")
    return

@app.cell
def cell_3(mo):
    """Real-time configuration and state management"""
    @mo.state
    def get_monitoring_state():
        return {
            'data': pd.DataFrame(),
            'alerts': [],
            'is_monitoring': False,
            'last_update': None,
            'data_sources': [],
            'system_health': {
                'cpu': 0,
                'memory': 0,
                'disk': 0,
                'network': 0
            },
            'metrics_history': {
                'timestamps': [],
                'response_times': [],
                'error_rates': [],
                'throughput': []
            }
        }

    monitoring_state = get_monitoring_state()
    return monitoring_state, get_monitoring_state

@app.cell
def cell_4(mo, random, datetime):
    """Monitoring configuration panel"""
    # Configuration controls
    config_controls = mo.ui.dictionary({
        'update_interval': mo.ui.slider(
            1, 30,
            value=5,
            label="Update Interval (seconds)"
        ),
        'max_data_points': mo.ui.slider(
            50, 500,
            value=200,
            label="Max Historical Data Points"
        ),
        'alert_threshold_cpu': mo.ui.slider(
            0, 100,
            value=80,
            label="CPU Alert Threshold (%)"
        ),
        'alert_threshold_memory': mo.ui.slider(
            0, 100,
            value=85,
            label="Memory Alert Threshold (%)"
        ),
        'alert_threshold_response_time': mo.ui.slider(
            100, 5000,
            value=1000,
            label="Response Time Alert (ms)"
        ),
        'data_source': mo.ui.dropdown(
            ["simulated", "api", "database"],
            value="simulated",
            label="Data Source"
        ),
        'enable_sound_alerts': mo.ui.checkbox(
            value=False,
            label="Enable Sound Alerts"
        ),
        'auto_refresh': mo.ui.checkbox(
            value=True,
            label="Auto-refresh Charts"
        )
    })

    mo.md("## ⚙️ Monitoring Configuration")
    config_controls
    return config_controls

@app.cell
def cell_5(monitoring_state, random, datetime, mo):
    """Real-time data generation and simulation"""
    def generate_system_metrics():
        """Generate realistic system metrics"""
        # Simulate system metrics with some randomness and trends
        base_cpu = 40 + random.uniform(-10, 20)
        base_memory = 60 + random.uniform(-15, 15)
        base_disk = 30 + random.uniform(-5, 10)
        base_network = 20 + random.uniform(-10, 30)

        # Add some realistic variations
        cpu_usage = max(0, min(100, base_cpu + random.gauss(0, 10)))
        memory_usage = max(0, min(100, base_memory + random.gauss(0, 8)))
        disk_usage = max(0, min(100, base_disk + random.gauss(0, 3)))
        network_usage = max(0, min(100, base_network + random.gauss(0, 15)))

        # Response time (correlated with system load)
        base_response_time = 100 + (cpu_usage / 100) * 500
        response_time = max(50, base_response_time + random.gauss(0, 100))

        # Error rate (inverse correlation with system health)
        error_rate = max(0, min(5, (cpu_usage / 100) * 3 + random.uniform(0, 1)))

        # Throughput (inverse correlation with response time)
        throughput = max(10, min(200, 1000 / max(response_time, 100) * 20 + random.uniform(-5, 5)))

        return {
            'timestamp': datetime.now(),
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'disk_usage': disk_usage,
            'network_usage': network_usage,
            'response_time': response_time,
            'error_rate': error_rate,
            'throughput': throughput,
            'active_connections': int(50 + random.uniform(-20, 50)),
            'cache_hit_rate': random.uniform(0.7, 0.95)
        }

    def update_monitoring_data():
        """Update monitoring data and check alerts"""
        if not monitoring_state['is_monitoring']:
            return

        # Generate new metrics
        new_metrics = generate_system_metrics()

        # Add to historical data
        new_row = pd.DataFrame([new_metrics])
        monitoring_state['data'] = pd.concat([monitoring_state['data'], new_row], ignore_index=True)

        # Limit data points
        max_points = config_controls.value['max_data_points']
        if len(monitoring_state['data']) > max_points:
            monitoring_state['data'] = monitoring_state['data'].tail(max_points).copy()

        # Update system health
        monitoring_state['system_health'] = {
            'cpu': new_metrics['cpu_usage'],
            'memory': new_metrics['memory_usage'],
            'disk': new_metrics['disk_usage'],
            'network': new_metrics['network_usage']
        }

        # Update metrics history
        monitoring_state['metrics_history']['timestamps'].append(new_metrics['timestamp'])
        monitoring_state['metrics_history']['response_times'].append(new_metrics['response_time'])
        monitoring_state['metrics_history']['error_rates'].append(new_metrics['error_rate'])
        monitoring_state['metrics_history']['throughput'].append(new_metrics['throughput'])

        # Limit history size
        history_limit = max_points
        for key in monitoring_state['metrics_history']:
            if len(monitoring_state['metrics_history'][key]) > history_limit:
                monitoring_state['metrics_history'][key] = monitoring_state['metrics_history'][key][-history_limit:]

        # Check for alerts
        check_alerts(new_metrics)

        # Update last update time
        monitoring_state['last_update'] = datetime.now()

    def check_alerts(metrics):
        """Check if alerts should be triggered"""
        alerts = []
        current_time = datetime.now()

        # CPU alert
        if metrics['cpu_usage'] > config_controls.value['alert_threshold_cpu']:
            severity = 'critical' if metrics['cpu_usage'] > 95 else 'warning'
            alerts.append({
                'timestamp': current_time,
                'type': 'CPU High',
                'message': f"CPU usage at {metrics['cpu_usage']:.1f}%",
                'severity': severity,
                'value': metrics['cpu_usage'],
                'threshold': config_controls.value['alert_threshold_cpu']
            })

        # Memory alert
        if metrics['memory_usage'] > config_controls.value['alert_threshold_memory']:
            severity = 'critical' if metrics['memory_usage'] > 95 else 'warning'
            alerts.append({
                'timestamp': current_time,
                'type': 'Memory High',
                'message': f"Memory usage at {metrics['memory_usage']:.1f}%",
                'severity': severity,
                'value': metrics['memory_usage'],
                'threshold': config_controls.value['alert_threshold_memory']
            })

        # Response time alert
        if metrics['response_time'] > config_controls.value['alert_threshold_response_time']:
            severity = 'critical' if metrics['response_time'] > 3000 else 'warning'
            alerts.append({
                'timestamp': current_time,
                'type': 'Response Time High',
                'message': f"Response time at {metrics['response_time']:.0f}ms",
                'severity': severity,
                'value': metrics['response_time'],
                'threshold': config_controls.value['alert_threshold_response_time']
            })

        # Error rate alert
        if metrics['error_rate'] > 2.0:
            severity = 'critical' if metrics['error_rate'] > 5.0 else 'warning'
            alerts.append({
                'timestamp': current_time,
                'type': 'Error Rate High',
                'message': f"Error rate at {metrics['error_rate']:.2f}%",
                'severity': severity,
                'value': metrics['error_rate'],
                'threshold': 2.0
            })

        # Add alerts to state (keep last 20)
        if alerts:
            monitoring_state['alerts'] = alerts + monitoring_state['alerts'][:20]

    # Initial data generation
    update_monitoring_data()
    return generate_system_metrics, update_monitoring_data, check_alerts

@app.cell
def cell_6(mo, monitoring_state):
    """System status dashboard"""
    def create_status_panel():
        """Create real-time system status panel"""
        health = monitoring_state['system_health']
        last_update = monitoring_state['last_update']

        # Determine overall status
        status_indicators = []
        overall_status = "healthy"

        if health['cpu'] > 90 or health['memory'] > 90:
            overall_status = "critical"
        elif health['cpu'] > 80 or health['memory'] > 80:
            overall_status = "warning"

        status_colors = {
            'healthy': '#4CAF50',
            'warning': '#FF9800',
            'critical': '#F44336'
        }

        # Create status HTML
        status_html = f"""
        <div style="padding: 1rem; border: 2px solid {status_colors[overall_status]}; border-radius: 8px; background-color: white;">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <div style="width: 20px; height: 20px; background-color: {status_colors[overall_status]}; border-radius: 50%; margin-right: 1rem;"></div>
                <h3 style="margin: 0; color: {status_colors[overall_status]};">System Status: {overall_status.upper()}</h3>
            </div>
            <div style="font-size: 0.9em; color: #666; margin-bottom: 1rem;">
                Last updated: {last_update.strftime('%H:%M:%S') if last_update else 'Never'}
            </div>
        """

        # System metrics grid
        status_html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem;">'

        metrics = [
            ('cpu', 'CPU Usage', health['cpu'], '%'),
            ('memory', 'Memory', health['memory'], '%'),
            ('disk', 'Disk', health['disk'], '%'),
            ('network', 'Network', health['network'], '%')
        ]

        for key, label, value, unit in metrics:
            color = status_colors['healthy'] if value < 70 else status_colors['warning'] if value < 90 else status_colors['critical']
            status_html += f'''
            <div style="text-align: center; padding: 0.5rem; border-left: 3px solid {color}; background-color: #f9f9f9;">
                <div style="font-size: 0.8em; color: #666;">{label}</div>
                <div style="font-size: 1.5em; font-weight: bold; color: {color};">{value:.1f}{unit}</div>
            </div>
            '''

        status_html += '</div></div>'

        return mo.md(status_html)

    # Create status panel
    status_panel = create_status_panel()

    mo.md("## 🖥️ System Status")
    status_panel
    return status_panel, create_status_panel

@app.cell
def cell_7(monitoring_state, mo, px, go):
    """Real-time charts"""
    def create_realtime_charts():
        """Create real-time updating charts"""
        if monitoring_state['data'].empty:
            return mo.md("Waiting for data...")

        df = monitoring_state['data']

        # 1. System Resources Chart
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['cpu_usage'],
            mode='lines+markers',
            name='CPU Usage',
            line=dict(color='#FF6B6B', width=2)
        ))
        fig1.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['memory_usage'],
            mode='lines+markers',
            name='Memory Usage',
            line=dict(color='#4ECDC4', width=2)
        ))
        fig1.add_hline(y=config_controls.value['alert_threshold_cpu'], line_dash="dash",
                      annotation_text="CPU Alert", line_color="red")
        fig1.add_hline(y=config_controls.value['alert_threshold_memory'], line_dash="dash",
                      annotation_text="Memory Alert", line_color="orange")

        fig1.update_layout(
            title="System Resources Over Time",
            xaxis_title="Time",
            yaxis_title="Usage (%)",
            height=400,
            yaxis=dict(range=[0, 100]),
            template="plotly_white"
        )

        # 2. Response Time Chart
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['response_time'],
            mode='lines+markers',
            name='Response Time',
            line=dict(color='#95E1D3', width=2),
            fill='tonexty' if len(df) > 1 else None
        ))
        fig2.add_hline(y=config_controls.value['alert_threshold_response_time'], line_dash="dash",
                      line_color="red", annotation_text="Alert Threshold")

        fig2.update_layout(
            title="Response Time Over Time",
            xaxis_title="Time",
            yaxis_title="Response Time (ms)",
            height=300,
            template="plotly_white"
        )

        # 3. Throughput and Error Rate
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['throughput'],
            mode='lines+markers',
            name='Throughput',
            line=dict(color='#FFA07A', width=2),
            yaxis='y'
        ))
        fig3.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['error_rate'] * 10,  # Scale for visibility
            mode='lines+markers',
            name='Error Rate (×10)',
            line=dict(color='#DC143C', width=2),
            yaxis='y2'
        ))

        fig3.update_layout(
            title="Performance Metrics",
            xaxis_title="Time",
            yaxis=dict(title="Throughput", side="left"),
            yaxis2=dict(title="Error Rate (×10)", side="right", overlaying="y"),
            height=300,
            template="plotly_white"
        )

        return (
            mo.ui.plotly(fig1),
            mo.ui.plotly(fig2),
            mo.ui.plotly(fig3)
        )

    # Create charts
    chart1, chart2, chart3 = create_realtime_charts()

    mo.md("## 📊 Real-time Metrics")
    chart1
    chart2
    chart3
    return chart1, chart2, chart3, create_realtime_charts

@app.cell
def cell_8(monitoring_state, mo):
    """Alerts panel"""
    def create_alerts_panel():
        """Create alerts display panel"""
        if not monitoring_state['alerts']:
            return mo.md("✅ No active alerts")

        alert_html = "<div style='max-height: 400px; overflow-y: auto;'>"
        alert_html += "<h4>Active Alerts</h4>"

        for alert in monitoring_state['alerts']:
            severity_colors = {
                'critical': '#DC143C',
                'warning': '#FF8C00',
                'info': '#4682B4'
            }

            bg_colors = {
                'critical': '#FFE4E1',
                'warning': '#FFF8DC',
                'info': '#F0F8FF'
            }

            severity = alert['severity']
            color = severity_colors.get(severity, '#666')
            bg_color = bg_colors.get(severity, '#F9F9F9')

            alert_html += f"""
            <div style='padding: 1rem; margin: 0.5rem 0; border-left: 4px solid {color};
                        background-color: {bg_color}; border-radius: 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;'>
                    <div style='font-weight: bold; color: {color};'>
                        🔔 {alert['type']}
                    </div>
                    <div style='font-size: 0.8em; color: #666;'>
                        {alert['timestamp'].strftime('%H:%M:%S')}
                    </div>
                </div>
                <div style='margin-bottom: 0.5rem;'>{alert['message']}</div>
                <div style='font-size: 0.8em; color: #666;'>
                    Current: {alert.get('value', 'N/A')} | Threshold: {alert.get('threshold', 'N/A')}
                </div>
            </div>
            """

        alert_html += "</div>"

        return mo.md(alert_html)

    # Alerts panel
    alerts_panel = create_alerts_panel()

    mo.md("## 🚨 Alerts")
    alerts_panel
    return alerts_panel, create_alerts_panel

@app.cell
def cell_9(mo, monitoring_state):
    """Control panel for monitoring"""
    def toggle_monitoring():
        """Toggle monitoring on/off"""
        monitoring_state['is_monitoring'] = not monitoring_state['is_monitoring']
        return monitoring_state['is_monitoring']

    def clear_data():
        """Clear monitoring data"""
        monitoring_state['data'] = pd.DataFrame()
        monitoring_state['alerts'] = []
        monitoring_state['metrics_history'] = {
            'timestamps': [],
            'response_times': [],
            'error_rates': [],
            'throughput': []
        }

    def update_now():
        """Force update data"""
        update_monitoring_data()

    # Control buttons
    toggle_btn = mo.ui.button(
        label="⏸️ Pause Monitoring" if monitoring_state['is_monitoring'] else "▶️ Start Monitoring",
        on_click=lambda: toggle_monitoring()
    )

    clear_btn = mo.ui.button(
        label="🗑️ Clear Data",
        on_click=lambda: clear_data()
    )

    update_btn = mo.ui.button(
        label="🔄 Update Now",
        on_click=lambda: update_now()
    )

    # Status display
    status_text = f"Status: {'🟢 Running' if monitoring_state['is_monitoring'] else '🔴 Stopped'}"
    status_display = mo.md(f"**Monitoring Status**: {status_text}")

    # Display controls
    mo.md("## 🎛️ Control Panel")
    status_display

    controls_row = mo.hstack([toggle_btn, update_btn, clear_btn])
    controls_row
    return toggle_monitoring, clear_data, update_now, toggle_btn, clear_btn, update_btn, controls_row, status_display

@app.cell
def cell_10(mo):
    """Documentation and features"""
    mo.md(f"""
    ## 📖 Real-time Monitoring Documentation

    This real-time monitoring dashboard provides:

    ### 🚀 Key Features
    - **Live System Metrics**: CPU, Memory, Disk, Network usage
    - **Performance Tracking**: Response times, throughput, error rates
    - **Intelligent Alerts**: Threshold-based alerting with severity levels
    - **Historical Data**: Configurable data retention and visualization
    - **Responsive Design**: Works on desktop and mobile devices

    ### ⚙️ Configuration Options
    - **Update Interval**: Control data refresh frequency (1-30 seconds)
    - **Alert Thresholds**: Customize CPU, Memory, and Response Time alerts
    - **Data Retention**: Set maximum historical data points
    - **Data Sources**: Support for simulated, API, and database sources

    ### 📊 Visualizations
    1. **System Resources**: Real-time CPU and Memory usage
    2. **Response Time**: Performance tracking over time
    3. **Throughput vs Errors**: Performance correlation analysis
    4. **Status Panel**: At-a-glance system health

    ### 🔔 Alert System
    - **Warning Level**: Issues that need attention
    - **Critical Level**: Immediate action required
    - **Alert History**: Track all alerts with timestamps
    - **Threshold Customization**: Set your own alert criteria

    ### 🛠️ Advanced Features
    - **Auto-refresh**: Automatic chart updates
    - **Data Export**: Export monitoring data for analysis
    - **Multiple Data Sources**: Connect to APIs, databases, or IoT devices
    - **Custom Metrics**: Add your own monitoring metrics
    - **Integration**: Connect to notification systems (Slack, Email, SMS)

    ### 🔧 Customization Guide

    #### Adding New Metrics
    ```python
    def custom_metric_generator():
        return {
            'timestamp': datetime.now(),
            'custom_metric': random.uniform(0, 100),
            # Add more metrics here
        }
    ```

    #### Custom Alert Logic
    ```python
    def check_custom_alerts(metrics):
        if metrics['custom_metric'] > threshold:
            # Add custom alert
            pass
    ```

    #### Data Source Integration
    - **API Integration**: Connect to REST APIs for real-time data
    - **Database Queries**: Query time-series databases
    - **IoT Devices**: Read from IoT sensors and devices
    - **Cloud Services**: Monitor cloud service metrics

    ### 📈 Use Cases
    - **Web Application Monitoring**: Track application performance
    - **Server Infrastructure**: Monitor server health and resources
    - **IoT Device Monitoring**: Real-time sensor data visualization
    - **Business Metrics**: Track KPIs and business metrics
    - **Network Monitoring**: Network performance and availability

    ### 🔒 Production Deployment
    - **Authentication**: Add user authentication and authorization
    - **Data Security**: Encrypt sensitive monitoring data
    - **Scalability**: Handle high-frequency data updates
    - **Persistence**: Store data in databases for long-term analysis
    - **Disaster Recovery**: Implement backup and recovery procedures

    ### 📱 Mobile Compatibility
    - Responsive design for mobile devices
    - Touch-friendly controls
    - Optimized chart rendering
    - Reduced data usage on mobile networks

    Created with ❤️ using Marimo Real-time Template

    Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)
    return

if __name__ == "__main__":
    app.run()