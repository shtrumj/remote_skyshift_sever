# User Management Scripts

This document describes the user creation scripts available for the Remote Agent Manager.

## Scripts Overview

### 1. `create_user.py` - Full Featured User Creation

A comprehensive user creation script with command-line argument parsing and additional options.

**Features:**
- Command-line argument parsing with `argparse`
- Optional email and full name parameters
- Input validation
- Verbose output option
- Detailed error messages
- Help documentation

**Usage:**
```bash
# Basic usage
python create_user.py <username> <password>

# With optional parameters
python create_user.py <username> <password> --email <email> --full-name "<full_name>"

# Verbose output
python create_user.py <username> <password> --verbose
```

**Examples:**
```bash
# Create admin user
python create_user.py admin password123

# Create user with email and full name
python create_user.py john password123 --email john@example.com --full-name "John Doe"

# Create user with verbose output
python create_user.py jane password123 --email jane@example.com --full-name "Jane Smith" --verbose
```

**Options:**
- `--email, -e`: Email address (default: username@example.com)
- `--full-name, -f`: Full name (default: username)
- `--verbose, -v`: Verbose output
- `--help, -h`: Show help message

### 2. `create_user_simple.py` - Simple User Creation

A simplified version for quick user creation with minimal parameters.

**Features:**
- Simple command-line interface
- Just username and password required
- Quick and easy to use
- Basic validation

**Usage:**
```bash
python create_user_simple.py <username> <password>
```

**Examples:**
```bash
# Create a simple user
python create_user_simple.py testuser password123

# Create admin user
python create_user_simple.py admin admin123
```

## Validation Rules

Both scripts enforce the following validation rules:

- **Username**: Minimum 3 characters
- **Password**: Minimum 6 characters
- **Uniqueness**: Username and email must be unique
- **Database**: User is saved to SQLite database

## Output

Successful user creation will display:

```
✅ User 'username' created successfully!
Login URL: http://localhost:4433/ui/login
Username: username
Password: password
```

## Error Handling

The scripts handle various error conditions:

- **User already exists**: `❌ User 'username' already exists!`
- **Email already registered**: `❌ Email 'email' is already registered!`
- **Invalid username**: `❌ Username must be at least 3 characters long!`
- **Invalid password**: `❌ Password must be at least 6 characters long!`
- **Database errors**: Detailed error messages

## Database Integration

Both scripts integrate with the existing authentication system:

- Uses `database.py` for database operations
- Uses `auth.py` for password hashing
- Creates users compatible with the web interface
- Supports all user management features

## Security Features

- **Password hashing**: Uses bcrypt for secure password storage
- **Input validation**: Prevents invalid data
- **Uniqueness checks**: Prevents duplicate users
- **Error handling**: Secure error messages

## Integration with Web Interface

Users created with these scripts can immediately:

1. **Login** at `http://localhost:4433/ui/login`
2. **Access profile** at `http://localhost:4433/ui/profile`
3. **Manage account** through the web interface
4. **Use all features** of the Remote Agent Manager

## Troubleshooting

### Common Issues

1. **"User already exists"**
   - Choose a different username
   - Use the web interface to manage existing users

2. **"Email already registered"**
   - Use a different email address
   - Or omit the email parameter to use default

3. **"Database error"**
   - Ensure the server is not running
   - Check database file permissions
   - Verify database schema

4. **"Import error"**
   - Ensure you're running from the project root directory
   - Check that all required modules are installed

### Getting Help

For the full-featured script:
```bash
python create_user.py --help
```

For the simple script:
```bash
python create_user_simple.py
# (will show usage if no arguments provided)
```

## Best Practices

1. **Use strong passwords**: Minimum 6 characters, but longer is better
2. **Use descriptive usernames**: Easy to identify and manage
3. **Provide email addresses**: Useful for account recovery
4. **Use full names**: Better for user management
5. **Test login**: Always verify the user can login after creation

## Script Comparison

| Feature | `create_user.py` | `create_user_simple.py` |
|---------|------------------|-------------------------|
| Command-line parsing | ✅ Full argparse | ❌ Basic sys.argv |
| Email option | ✅ Optional | ❌ Auto-generated |
| Full name option | ✅ Optional | ❌ Auto-generated |
| Verbose output | ✅ Available | ❌ Not available |
| Help documentation | ✅ Comprehensive | ❌ Basic |
| Error handling | ✅ Detailed | ✅ Basic |
| Use case | Production/admin | Quick testing |

Choose the script that best fits your needs:
- **`create_user.py`**: For production use and user management
- **`create_user_simple.py`**: For quick testing and development 