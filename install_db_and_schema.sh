brew install postgresql
brew services start postgresql

createdb standup_db

psql -d standup_db -c "CREATE USER standup_user WITH PASSWORD 'Pa$$sw0rd~';"
psql -d standup_db -c "GRANT ALL PRIVILEGES ON DATABASE standup_db TO standup_user;"
