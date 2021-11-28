from server import app


@app.cli.command()
def test():
    import unittest
    import sys
    tests = unittest.TestLoader().discover("tests")
    result = unittest.TextTestRunner(verbosity=2).run(tests)
    if result.errors or result.failures:
        sys.exit(1)


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
