"""
CyberRFP Maroc - Application Entrypoint
Runs the production ASGI Uvicorn server on port 8000.
"""
import uvicorn
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    print("=" * 60)
    print("🛡️  CyberRFP Maroc - Serveur de Veille Cybersécurité")
    print(f"🌐  Accès Dashboard: http://localhost:{port}")
    print("🔑  Identifiants par défaut: admin / cyberrfp2026")
    print("=" * 60)
    uvicorn.run("src.server:app", host=host, port=port, reload=False)
