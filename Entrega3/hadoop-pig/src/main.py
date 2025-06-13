from hadoop_pig_service import HadoopPigService
import time

service = HadoopPigService()

def main():
    while True:
        # Aquí podrías escuchar una cola o esperar archivos
        # Ejemplo simplificado:
        result = service.ejecutar_script_pig(
            '/data/scripts/processing.pig',
            {'input': '/input/data.csv', 'output': '/output/results'}
        )
        print(result)
        time.sleep(120)

if __name__ == "__main__":
    main()