web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
worker: celery -A app.worker.celery_app worker --loglevel=info
streamlit: streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0