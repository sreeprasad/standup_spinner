# 🎯 Standup Spinner

A fun and interactive web application to randomize the order of your daily standup meetings! 

## ✨ Features

- **🎰 Interactive Spinner**: Spin the wheel to get a random standup order
- **🎭 Fun Twists**: Add variety with different twist options:
  - Reverse Order
  - Random Skip
  - Someone Goes Twice
  - Pair Up
- **👥 Team Management**: Easily add/remove team members with custom emojis
- **📊 Statistics**: Track participation and see fun stats about your standups
- **🎨 Beautiful UI**: Clean, modern interface built with Tailwind CSS
- **⚡ Real-time Updates**: Uses HTMX for smooth, dynamic interactions



## 📋 Prerequisites

- Python 3.13+
- PostgreSQL
- Git
- uv (Python package manager)

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd standup-spinner
```

### 2. Set Up PostgreSQL

Make sure PostgreSQL is running:

```bash
# On macOS with Homebrew
brew services start postgresql

# Create database and user
psql postgres
```

In the PostgreSQL prompt:
```sql
CREATE DATABASE standup_db;
CREATE USER standup_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE standup_db TO your_user_id;
\q
```

### 3. Backend Setup

```bash
cd backend

# Initialize Python project with uv
uv init --python 3.13.5

# Add dependencies
uv add fastapi uvicorn sqlalchemy psycopg2-binary python-multipart python-dotenv

# Create environment file
echo "DATABASE_URL=postgresql://standup_user:your_secure_password@localhost/standup_db" > .env

# Start the backend server
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend Setup

```bash
cd ../frontend

# Start the frontend server
python3 -m http.server 8080
```

### 5. Access the Application

- **Frontend**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🎮 How to Use

1. **Add Team Members**: Enter names and optional emojis for your team
2. **Choose a Twist**: Select from various fun options to spice up your standup
3. **Spin the Wheel**: Click the big spin button and watch the magic happen!
4. **Follow the Order**: Use the generated order for your standup meeting
5. **Track Stats**: View participation statistics and patterns

## 🎭 Available Twists

- **No Twist**: Simple random order
- **Reverse Order**: Alphabetical order, but reversed
- **Random Skip**: One random person gets skipped
- **Someone Goes Twice**: Lucky person gets to go twice!
- **Pair Up**: People are paired together for joint updates

## 📂 Project Structure

```
standup-spinner/
├── backend/
│   ├── main.py              
│   ├── pyproject.toml       
│   ├── .env                 
│   └── README.md           
├── frontend/
│   └── index.html          
└── README.md               
```

## 🚀 Deployment

### Vercel Deployment (Coming Soon)

This project is ready for deployment to Vercel! The frontend can be deployed as a static site, and the backend can be deployed as a serverless function.

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
DATABASE_URL=postgresql://username:password@hostname:port/database_name
```

### Database Schema

The application automatically creates the following tables:
- `team_members` - Stores team member information
- `spin_orders` - Tracks standup session history

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 API Endpoints

- `GET /` - Welcome page
- `GET /docs` - Interactive API documentation
- `GET /members/` - List all active team members
- `POST /members/` - Add a new team member
- `DELETE /members/{member_id}` - Remove a team member
- `POST /spin/` - Spin the standup wheel
- `GET /stats/` - Get participation statistics
- `GET /twists/` - Get available twist options

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error**
- Ensure PostgreSQL is running
- Check database credentials in `.env` file
- Verify database and user exist

**CORS Errors**
- Backend server must be running on port 8000
- Frontend server must be running on port 8080

**Port Already in Use**
- Kill existing processes: `pkill -f "python -m http.server"`
- Use different ports if needed

## 🎉 Have Fun!

Remember, the goal is to make your standup meetings more engaging and fun. Don't take the twists too seriously - they're meant to add a bit of humor and variety to your daily routine!

---

**Made by sp!**
