job-copilot/
├── backend/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Environment variables and settings
│   ├── database.py          # SQLAlchemy setup
│   ├── models.py            # Database models
│   ├── schemas.py           # Pydantic schemas for API
│   ├── auth.py              # JWT authentication
│   ├── __init__.py 
│   ├── init_db.py       
│   ├── routers/
│   ├   | __pyache__
│   │   ├── __init__.py
│   │   ├── users.py         # User registration/login
│   │   └── applications.py  # Main application logic
│   ├── agents/
│   ├   | __pyache__
│   │   ├── __init__.py
│   │   ├── orchestrator.py  # LangGraph workflow
│   │   ├── fit_analyst.py   # Fit analysis agent
│   │   ├── resume_writer.py # Resume rewriting agent
│   │   ├── cover_letter.py  # Cover letter agent
│   │   └── interviewer.py   # Interview Q&A agent
│   ├── services/
│   ├   | __pyache__
│   │   ├── __init__.py
│   │   ├── pdf_parser.py    # Resume PDF parsing
│   │   ├── jd_scraper.py    # LinkedIn/URL scraping
│   │   └── document_gen.py  # DOCX/PDF generation
│   └         
├── frontend/
│   ├── index.html           # Main page
│   ├── styles.css           # All styling
│   ├── app.js               # Main application logic
│   ├── config.js            # Global URL to access
│   └── components/
│       ├── auth.js          # Login/register handling
│       ├── upload.js        # File upload handling
│       ├── roles.js         # Roles list view
│       └── diff.js          # Diff view component
├── requirements.txt
├── .env                     # Environment variables 
├── .env.example             # Template for .env
└── README.md
└──── copilot.db 			 # SQLite database (auto-created)
└──render.yaml				 # render config
