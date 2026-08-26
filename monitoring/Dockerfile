FROM prom/prometheus:v2.51.0 as prometheus_base

FROM grafana/grafana:10.4.0

USER root

# Copy Prometheus binary and default configs
COPY --from=prometheus_base /bin/prometheus /usr/local/bin/prometheus
COPY --from=prometheus_base /bin/promtool /usr/local/bin/promtool

RUN mkdir -p /etc/prometheus /data/prometheus /etc/grafana/provisioning \
    && chown -R grafana:root /etc/prometheus /data/prometheus /etc/grafana

COPY prometheus.yml /etc/prometheus/prometheus.yml
COPY provisioning /etc/grafana/provisioning
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV GF_SECURITY_ADMIN_USER=admin
ENV GF_SECURITY_ADMIN_PASSWORD=AdminPassword123!
ENV GF_USERS_ALLOW_SIGN_UP=false
ENV GF_AUTH_ANONYMOUS_ENABLED=true
ENV GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer
ENV GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-piechart-panel

USER grafana

EXPOSE 3000 9090

ENTRYPOINT ["/entrypoint.sh"]
