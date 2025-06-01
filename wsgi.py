from app import app


if __name__ == '__main__':
    # Set host to '0.0.0.0' to be accessible from other devices on the network,
    # or '127.0.0.1' (localhost) for local access only.
    # debug=True allows for automatic reloading on code changes and provides debugger info.
    app.run(debug=True)