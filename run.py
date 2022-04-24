import uvicorn
from dotenv import load_dotenv
load_dotenv()

if __name__ == '__main__':
  uvicorn.run("app:app", host='0.0.0.0', port=5001, reload=True, debug=True, workers=2)