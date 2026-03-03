from src.app import build_app

def main():
    app, nav, main_menu = build_app()
    nav.push(main_menu)
    app.run()

if __name__ == "__main__":
    main()
