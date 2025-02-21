ARG PYTHON_VERSION=3.11.4
ARG DEBIAN_BASE=bookworm
FROM python:${PYTHON_VERSION}-slim-${DEBIAN_BASE} AS base

COPY resources/nginx-template.conf /templates/nginx/frappe.conf.template
COPY resources/nginx-entrypoint.sh /usr/local/bin/nginx-entrypoint.sh
COPY nvm/install.sh .

ARG WKHTMLTOPDF_VERSION=0.12.6.1-3
ARG WKHTMLTOPDF_DISTRO=bookworm
ARG NODE_VERSION=18.20.0
ENV NVM_DIR=/home/frappe/.nvm
ENV PATH ${NVM_DIR}/versions/node/v${NODE_VERSION}/bin/:${PATH}

RUN useradd -ms /bin/bash frappe \
    && apt-get update \
    && apt-get install --no-install-recommends -y \
    curl \
    git \
    vim \
    nginx \
    gettext-base \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    restic \
    mariadb-client \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libgtk-4-1 \
    libnspr4 \
    libnss3 \
    libu2f-udev \
    libvulkan1 \
    libxcomposite1 \
    libxfixes3 \
    libxdamage1 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libpq-dev \
    postgresql-client \
    wait-for-it \
    jq \
    && apt-get install -y wget \
    && mkdir -p ${NVM_DIR} \
    && chmod 755 install.sh \
    && ./install.sh \
    && . ${NVM_DIR}/nvm.sh \
    && nvm install ${NODE_VERSION} \
    && nvm use v${NODE_VERSION} \
    && npm install -g npm@10.8.1 \
    && npm install -g yarn \
    && nvm alias default v${NODE_VERSION} \
    && rm -rf ${NVM_DIR}/.cache \
    && echo 'export NVM_DIR="/home/frappe/.nvm"' >>/home/frappe/.bashrc \
    && echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"  # This loads nvm' >>/home/frappe/.bashrc \
    && echo '[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"  # This loads nvm bash_completion' >>/home/frappe/.bashrc \
    && if [ "$(uname -m)" = "aarch64" ]; then export ARCH=arm64; fi \
    && if [ "$(uname -m)" = "x86_64" ]; then export ARCH=amd64; fi \
    && downloaded_file=wkhtmltox_${WKHTMLTOPDF_VERSION}.${WKHTMLTOPDF_DISTRO}_${ARCH}.deb \
    && curl -sLO https://github.com/wkhtmltopdf/packaging/releases/download/$WKHTMLTOPDF_VERSION/$downloaded_file \
    && apt-get install -y ./$downloaded_file \
    && rm $downloaded_file \
    && rm -rf /var/lib/apt/lists/* \
    && rm -fr /etc/nginx/sites-enabled/default \
    && pip3 install frappe-bench \
   && sed -i '/user www-data/d' /etc/nginx/nginx.conf \
   && ln -sf /dev/stdout /var/log/nginx/access.log && ln -sf /dev/stderr /var/log/nginx/error.log \
   && touch /run/nginx.pid \
   && chown -R frappe:frappe /etc/nginx/conf.d \
   && chown -R frappe:frappe /etc/nginx/nginx.conf \
   && chown -R frappe:frappe /var/log/nginx \
   && chown -R frappe:frappe /var/lib/nginx \
   && chown -R frappe:frappe /run/nginx.pid \
   && chmod +x /usr/local/bin/nginx-entrypoint.sh \
   && chmod 644 /templates/nginx/frappe.conf.template

FROM base AS builder

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends -y \
    wget \
    libpq-dev \
    libffi-dev \
    liblcms2-dev \
    libldap2-dev \
    libmariadb-dev \
    libsasl2-dev \
    libtiff5-dev \
    libwebp-dev \
    redis-tools \
    rlwrap \
    tk8.6-dev \
    cron \
    gcc \
    build-essential \
    libbz2-dev \
    && rm -rf /var/lib/apt/lists/*

USER frappe

ARG FRAPPE_BRANCH=version-15
ARG ERPNEXT_BRANCH=version-15
ARG HRMS_BRANCH=version-15
ARG KHUSHI_ERPNEXT_BRANCH=main
ARG WHATSAPP_PRO_BRANCH=main
ARG HRMS_PLUS_BRANCH=main
ARG INDIA_COMPLIANCE_BRANCH=version-15
ARG ECOMMERCE_BRANCH=main
ARG PRINT_DESIGNER_BRANCH=main
ARG FRAPPE_PATH=https://github.com/frappe/frappe
RUN bench init \
    --frappe-branch=${FRAPPE_BRANCH} \
    --frappe-path=${FRAPPE_PATH} \
    --no-procfile \
    --no-backups \
    --skip-redis-config-generation \
    --verbose \
    /home/frappe/frappe-bench && \
  cd /home/frappe/frappe-bench && \
  bench get-app erpnext --branch ${ERPNEXT_BRANCH} && \
  bench get-app hrms --branch ${HRMS_BRANCH} && \
  bench get-app https://github.com/TechInsights-ai-org/Khushi_erpnext.git --branch ${KHUSHI_ERPNEXT_BRANCH} && \
  bench get-app https://github.com/TechInsights-ai-org/HRMS-Plus.git --branch ${HRMS_PLUS_BRANCH} && \
  bench get-app https://github.com/TechInsights-ai-org/frappe_whatsapp_pro.git --branch ${WHATSAPP_PRO_BRANCH} && \
  bench get-app https://github.com/resilient-tech/india-compliance.git --branch ${INDIA_COMPLIANCE_BRANCH} && \
  bench get-app https://github.com/frappe/ecommerce_integrations.git --branch ${ECOMMERCE_BRANCH} && \
  bench get-app https://github.com/frappe/print_designer.git --branch ${PRINT_DESIGNER_BRANCH} && \
  bench build --app frappe && \
  echo "{}" > sites/common_site_config.json && \
  rm -rf ~/.git-credentials && \
  find apps -mindepth 1 -path "*/.git" | xargs rm -fr

FROM base as backend

USER frappe

COPY --from=builder --chown=frappe:frappe /home/frappe/frappe-bench /home/frappe/frappe-bench

WORKDIR /home/frappe/frappe-bench

VOLUME [ \
  "/home/frappe/frappe-bench/sites", \
  "/home/frappe/frappe-bench/sites/assets", \
  "/home/frappe/frappe-bench/logs" \
]

CMD [ \
  "/home/frappe/frappe-bench/env/bin/gunicorn", \
  "--chdir=/home/frappe/frappe-bench/sites", \
  "--bind=0.0.0.0:8000", \
  "--threads=4", \
  "--workers=2", \
  "--worker-class=gthread", \
  "--worker-tmp-dir=/dev/shm", \
  "--timeout=120", \
  "--preload", \
  "frappe.app:application" \
]
