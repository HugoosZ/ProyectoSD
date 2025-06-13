import os
import subprocess
from hdfs import InsecureClient
from dotenv import load_dotenv

load_dotenv(dotenv_path='hadoop.env')

class HadoopPigService:
    def __init__(self):
        self.hdfs_url = f"http://{os.getenv('HADOOP_HOST')}:{os.getenv('HADOOP_PORT')}"
        self.client = InsecureClient(self.hdfs_url, user='root')
        
    def ejecutar_script_pig(self, script_path, params=None):
        """
        Ejecuta un script Pig en el contenedor Hadoop
        
        Args:
            script_path (str): Ruta local al script Pig
            params (dict): Parámetros para el script
            
        Returns:
            dict: Resultado de la ejecución
        """
        try:
            # Copiar script a HDFS
            hdfs_script_path = f"/tmp/{os.path.basename(script_path)}"
            self.client.upload(hdfs_script_path, script_path)
            
            # Construir comando Pig
            cmd = ['pig', '-x', 'mapreduce', '-f', hdfs_script_path]
            
            if params:
                for k, v in params.items():
                    cmd.extend(['-param', f"{k}={v}"])
            
            # Ejecutar
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def leer_resultados(self, hdfs_path):
        """
        Lee resultados desde HDFS
        
        Args:
            hdfs_path (str): Ruta en HDFS a los resultados
            
        Returns:
            list: Contenido de los archivos resultantes
        """
        try:
            with self.client.read(hdfs_path) as reader:
                return reader.read().decode('utf-8').splitlines()
        except Exception as e:
            print(f"Error leyendo resultados: {e}")
            return []