#!/bin/bash

# Переменные из .env
PGUSER=tg_supply_cather
PGPASSWORD=Fhnbkkthbz7ZZ
PGDATABASE=supply_catcher
PGPORT=5432

# 1. Установка PostgreSQL
sudo apt update
sudo apt install -y postgresql postgresql-contrib

# 2. Создание пользователя и базы
sudo -u postgres psql <<EOF
DO
\$do\$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_user WHERE usename = '$PGUSER') THEN
      CREATE USER $PGUSER WITH PASSWORD '$PGPASSWORD';
   END IF;
END
\$do\$;

CREATE DATABASE $PGDATABASE OWNER $PGUSER;
GRANT ALL PRIVILEGES ON DATABASE $PGDATABASE TO $PGUSER;
EOF

# 3. Настройка postgresql.conf
PGCONF=$(find /etc/postgresql -name postgresql.conf)
sudo sed -i "s/^#listen_addresses =.*/listen_addresses = '*'/g" "$PGCONF"

# 4. Настройка pg_hba.conf
PGHBA=$(find /etc/postgresql -name pg_hba.conf)
sudo bash -c "echo 'host    all             all             0.0.0.0/0               md5' >> $PGHBA"

# 5. Открытие порта 5432 (UFW)
sudo ufw allow 5432/tcp

# 6. Перезапуск PostgreSQL
sudo systemctl restart postgresql

# 7. Проверка подключения
echo "🔁 Проверка подключения с psql:"
PGPASSWORD=$PGPASSWORD psql -h 127.0.0.1 -U $PGUSER -d $PGDATABASE -p $PGPORT -c '\conninfo'
