from uvicorn import run

from aeris.env import get_setting

if __name__ == "__main__":
    run(
        "aeris.main:app",
        host="0.0.0.0",
        port=int(get_setting("PORT", 8000)),
        reload=True,
        reload_includes=["aeris/schemas/schema.graphql"],
    )
