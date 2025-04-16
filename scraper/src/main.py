from waze_scraper import test_driver,obtener_eventos_waze

if __name__ == "__main__":
    driver = test_driver()
    eventos = obtener_eventos_waze(driver)
    
    for evento in eventos:
        print(evento)

