from app import build_app

def main():
    nav, main_menu = build_app()
    nav.push(main_menu)

if __name__ == "__main__":
    main()
