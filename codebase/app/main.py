from fastapi import FastAPI
from pathlib import Path
from app.controllers.prescription_controller import router as prescription_router
from app.controllers.reminder_controller import router as reminder_router

app = FastAPI(
    title="Long Chau Medicine Reminder MVC Backend",
    version="3.0.0"
)

app.include_router(reminder_router, prefix="/api/reminders", tags=["Reminder Home"])
app.include_router(prescription_router, prefix="/api/prescriptions", tags=["Prescriptions"])


@app.get("/")
def healthcheck():
    return {
        "status": "ok",
        "service": "Long Chau Medicine Reminder MVC Backend"
    }


if __name__ == "__main__":
    import uvicorn

    app_dir = Path(__file__).resolve().parent
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[str(app_dir)],
    )
