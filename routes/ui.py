"""
UI Routes for Remote Agent Manager
"""
from fastapi import APIRouter, Request, HTTPException, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from auth import get_current_active_user, User, UserCreate, UserLogin, create_access_token, get_password_hash, verify_password, SECRET_KEY, ALGORITHM
from database import db_manager
import uuid
from datetime import timedelta
from jose import JWTError, jwt

# Create router
router = APIRouter(prefix="/ui", tags=["UI"])

# Templates
templates = Jinja2Templates(directory="templates")

# Authentication routes
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    # Check for registration success message
    registration_success = request.cookies.get("registration_success")
    context = {"request": request}
    
    if registration_success:
        context["success"] = "Registration successful! Please wait for admin approval before logging in."
    
    response = templates.TemplateResponse("login.html", context)
    
    # Clear the cookie after showing the message
    if registration_success:
        response.delete_cookie(key="registration_success")
    
    return response

@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Handle login"""
    try:
        # Get user with password
        user_data = db_manager.get_user_with_password(username)
        if not user_data:
            return templates.TemplateResponse(
                "login.html", 
                {"request": request, "error": "Invalid username or password"}
            )
        
        # Verify password
        if not verify_password(password, user_data["hashed_password"]):
            return templates.TemplateResponse(
                "login.html", 
                {"request": request, "error": "Invalid username or password"}
            )
        
        # Check if user is active
        if not user_data["is_active"]:
            return templates.TemplateResponse(
                "login.html", 
                {"request": request, "error": "Account is disabled"}
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": user_data["username"]}, 
            expires_delta=access_token_expires
        )
        
        # Redirect to dashboard with token
        response = RedirectResponse(url="/ui/dashboard", status_code=302)
        response.set_cookie(
            key="access_token", 
            value=access_token, 
            httponly=True,
            secure=False,  # Allow HTTP for development
            samesite="lax"  # Allow cross-site requests
        )
        return response
        
    except Exception as e:
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": f"Login failed: {str(e)}"}
        )

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Registration page"""
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form("")
):
    """Handle registration"""
    try:
        # Check if user already exists
        existing_user = db_manager.get_user_by_username(username)
        if existing_user:
            return templates.TemplateResponse(
                "register.html", 
                {"request": request, "error": "Username already exists"}
            )
        
        existing_email = db_manager.get_user_by_email(email)
        if existing_email:
            return templates.TemplateResponse(
                "register.html", 
                {"request": request, "error": "Email already exists"}
            )
        
        # Create user
        user_data = {
            "id": str(uuid.uuid4()),
            "username": username,
            "email": email,
            "full_name": full_name if full_name else None,
            "hashed_password": get_password_hash(password),
            "is_active": True,
            "is_admin": False,
            "is_approved": False
        }
        
        db_manager.create_user(user_data)
        
        # Redirect to login with approval message
        response = RedirectResponse(url="/ui/login", status_code=302)
        response.set_cookie(key="registration_success", value="true", max_age=60)
        return response
        
    except Exception as e:
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "error": f"Registration failed: {str(e)}"}
        )

@router.get("/logout")
async def logout():
    """Handle logout"""
    response = RedirectResponse(url="/ui/login", status_code=302)
    response.delete_cookie(key="access_token")
    return response

# Protected UI routes
@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🔍 Dashboard access attempt from {request.client.host if request.client else 'unknown'}")
    
    # Check if user is authenticated
    access_token = request.cookies.get("access_token")
    if not access_token:
        logger.warning(f"❌ No access token found for dashboard access from {request.client.host}")
        return RedirectResponse(url="/ui/login", status_code=302)
    
    try:
        # Verify token
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            logger.warning(f"❌ No username in token for dashboard access from {request.client.host}")
            return RedirectResponse(url="/ui/login", status_code=302)
        
        # Check if user exists and is approved
        user_data = db_manager.get_user_by_username(username)
        if not user_data or not user_data.get("is_approved"):
            logger.warning(f"❌ User not found or not approved: {username} from {request.client.host}")
            return RedirectResponse(url="/ui/login", status_code=302)
        
        logger.info(f"✅ Dashboard access granted for user: {username} from {request.client.host}")
        return templates.TemplateResponse("dashboard.html", {"request": request})
    except JWTError as e:
        logger.error(f"❌ JWT error for dashboard access from {request.client.host}: {str(e)}")
        return RedirectResponse(url="/ui/login", status_code=302)

@router.get("/customers", response_class=HTMLResponse)
async def customers_page(request: Request):
    """Customers management page"""
    # Check if user is authenticated
    access_token = request.cookies.get("access_token")
    if not access_token:
        return RedirectResponse(url="/ui/login", status_code=302)
    
    try:
        # Verify token
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            return RedirectResponse(url="/ui/login", status_code=302)
        
        # Check if user exists and is approved
        user_data = db_manager.get_user_by_username(username)
        if not user_data or not user_data.get("is_approved"):
            return RedirectResponse(url="/ui/login", status_code=302)
        
        return templates.TemplateResponse("customers.html", {"request": request})
    except JWTError:
        return RedirectResponse(url="/ui/login", status_code=302)

@router.get("/scripts", response_class=HTMLResponse)
async def scripts_page(request: Request):
    """Scripts management page"""
    # Check if user is authenticated
    access_token = request.cookies.get("access_token")
    if not access_token:
        return RedirectResponse(url="/ui/login", status_code=302)
    
    try:
        # Verify token
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            return RedirectResponse(url="/ui/login", status_code=302)
        
        # Check if user exists and is approved
        user_data = db_manager.get_user_by_username(username)
        if not user_data or not user_data.get("is_approved"):
            return RedirectResponse(url="/ui/login", status_code=302)
        
        return templates.TemplateResponse("scripts.html", {"request": request})
    except JWTError:
        return RedirectResponse(url="/ui/login", status_code=302)

@router.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    """Users management page"""
    # Check if user is authenticated
    access_token = request.cookies.get("access_token")
    if not access_token:
        return RedirectResponse(url="/ui/login", status_code=302)
    
    try:
        # Verify token
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            return RedirectResponse(url="/ui/login", status_code=302)
        
        # Check if user exists and is approved
        user_data = db_manager.get_user_by_username(username)
        if not user_data or not user_data.get("is_approved"):
            return RedirectResponse(url="/ui/login", status_code=302)
        
        return templates.TemplateResponse("users.html", {"request": request})
    except JWTError:
        return RedirectResponse(url="/ui/login", status_code=302)

@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    """User profile page"""
    # Check if user is authenticated
    access_token = request.cookies.get("access_token")
    if not access_token:
        return RedirectResponse(url="/ui/login", status_code=302)
    
    try:
        # Verify token
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            return RedirectResponse(url="/ui/login", status_code=302)
        
        # Check if user exists and is approved
        user_data = db_manager.get_user_by_username(username)
        if not user_data or not user_data.get("is_approved"):
            return RedirectResponse(url="/ui/login", status_code=302)
        
        return templates.TemplateResponse("profile.html", {"request": request})
    except JWTError:
        return RedirectResponse(url="/ui/login", status_code=302)

@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Admin dashboard page"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🔍 Admin dashboard access attempt from {request.client.host if request.client else 'unknown'}")
    
    # Check if user is authenticated and is admin
    access_token = request.cookies.get("access_token")
    if not access_token:
        logger.warning(f"❌ No access token found for admin dashboard access from {request.client.host}")
        return RedirectResponse(url="/ui/login", status_code=302)
    
    try:
        # Verify token and check if user is admin
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            logger.warning(f"❌ No username in token for admin dashboard access from {request.client.host}")
            return RedirectResponse(url="/ui/login", status_code=302)
        
        user_data = db_manager.get_user_by_username(username)
        if not user_data or not user_data.get("is_admin"):
            logger.warning(f"❌ User not admin: {username} from {request.client.host}")
            return RedirectResponse(url="/ui/dashboard", status_code=302)
        
        logger.info(f"✅ Admin dashboard access granted for user: {username} from {request.client.host}")
        return templates.TemplateResponse("admin_dashboard.html", {"request": request})
    except JWTError as e:
        logger.error(f"❌ JWT error for admin dashboard access from {request.client.host}: {str(e)}")
        return RedirectResponse(url="/ui/login", status_code=302)



@router.get("/test", response_class=HTMLResponse)
async def test_page(request: Request):
    """Test page for debugging"""
    # Check if user is authenticated
    access_token = request.cookies.get("access_token")
    if not access_token:
        return RedirectResponse(url="/ui/login", status_code=302)
    
    try:
        # Verify token
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            return RedirectResponse(url="/ui/login", status_code=302)
        
        # Check if user exists and is approved
        user_data = db_manager.get_user_by_username(username)
        if not user_data or not user_data.get("is_approved"):
            return RedirectResponse(url="/ui/login", status_code=302)
        
        return templates.TemplateResponse("test_user_display.html", {"request": request})
    except JWTError:
        return RedirectResponse(url="/ui/login", status_code=302)

@router.get("/admin-test", response_class=HTMLResponse)
async def admin_test_page(request: Request):
    """Admin test page for debugging"""
    return templates.TemplateResponse("admin_test.html", {"request": request})

@router.get("/", response_class=HTMLResponse)
async def root_redirect():
    """Redirect root to dashboard"""
    return RedirectResponse(url="/ui/dashboard", status_code=302) 