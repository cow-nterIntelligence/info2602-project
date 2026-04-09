import typer
from sqlmodel import Session, select
from app.database import engine
from app.models.user import User

app = typer.Typer()

@app.command()
def create_user(username: str, password: str, email: str, role: str = "user"):
    """Create any user (useful for testing)"""
    with Session(engine) as session:
        existing = session.exec(select(User).where(User.username == username)).first()
        if existing:
            print(f"User {username} already exists")
            return
        
        user = User(
            username=username,
            email=email,
            password=password,
            role=role
        )
        session.add(user)
        session.commit()
        print(f"Created user: {username}")

@app.command()
def create_bob():
    """Create the required bob user"""
    create_user("bob", "bobpass", "bob@example.com", "user")

if __name__ == "__main__":
    app()