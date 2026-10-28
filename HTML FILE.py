
<!DOCTYPE html>
<html>
<head>
    <title>Login - Healthcare Analytics</title>
</head>
<body>
    <h1>Healthcare Analytics and Patient Risk Indicator System</h1>
    <h2>Login</h2>

    <form action="/login" method="POST">
        <label>Username:</label>
        <input type="text" name="username" required>
        <br><br>

        <label>Password:</label>
        <input type="password" name="password" required>
        <br><br>

        <button type="submit">Login</button>
    </form>

    <p>
        Don't have an account?
        <a href="/register">Create an account</a>
    </p>
</body>
</html>
