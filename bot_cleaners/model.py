from mesa.model import Model
from mesa.agent import Agent
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector
from collections import deque


import numpy as np
from queue import PriorityQueue
class Celda(Agent):
    def __init__(self, unique_id, model, sucia=False):
        super().__init__(unique_id, model)
        self.sucia = sucia


class EstacionCarga(Agent):
      def __init__(self, unique_id, model):
          super().__init__(unique_id, model)


class Mueble(Agent):
      def __init__(self, unique_id, model):
          super().__init__(unique_id, model)


class RobotLimpieza(Agent):
        TIEMPO_ESPERA = 5  # Definir un tiempo de espera
        LIMITE_REPLANIFICACIONES = 3  # Definir un límite de replanificaciones
        def __init__(self, unique_id, model):
            super().__init__(unique_id, model)
            self.sig_pos = None
            self.contador_espera = 0  # Inicializar el contador de espera
            self.movimientos = 0
            self.carga = 100
            self.umbral_bateria = 20  # Ejemplo de umbral de batería
            self.ruta_planeada = []  # Añadir para guardar la ruta planeada
            self.estacion_carga = None  # Añadir para ubicar la estación de carga
            self.necesita_cargar = True  # Or some initial value based on your logic



     
        def limpiar_celda_actual(self):
            contenido_celda_actual = self.model.grid.get_cell_list_contents(self.pos)
            for obj in contenido_celda_actual:
                if isinstance(obj, Celda) and obj.sucia:
                    obj.sucia = False  # Cambiar el estado de la celda a "limpia"
                    break  # Suponiendo que solo hay una celda en la posición

        def step(self):
            # Si el robot está cargando, incrementar la batería
            if self.estoy_cargando() == True :
                print(f"Robot {self.unique_id} is charging.")
                self.carga = min(100, self.carga + 25)  # Suponiendo que se carga un 25% por step
                return  # No hacer más acciones si está cargando

            # Planificar ruta hacia celda sucia si no hay ruta planeada
            if not self.ruta_planeada:
                celda_sucia = self.encontrar_celda_sucia_mas_cercana()
                if celda_sucia is not None:
                    self.ruta_planeada = [celda_sucia]
                else:
                    self.ruta_planeada = []
                self.verificar_ruta()


            # Verificar nivel de batería y planificar ruta hacia estación de carga si es necesario
            if self.carga < self.umbral_bateria: 
                estacion_cercana = self.encontrar_estacion_carga_mas_cercana()
                if estacion_cercana:
                    self.ruta_planeada = self.algoritmo_a_estrella(self.pos, estacion_cercana.pos)

            # Mover el robot a lo largo de la ruta planeada
            self.mover_a_siguiente_posicion_en_ruta()
            self.limpiar_celda_actual()  # Limpia la celda si es necesario
            # Comunicar ruta y resolver conflictos (aunque en tu caso no se comuniquen)
            # Suponiendo que tienes una función para comunicar la ruta planeada
            self.comunicar_ruta()
            self.actualizar_ruta()
            #self.resolver_deadlocks()
        def verificar_ruta(self):
            for pos in self.ruta_planeada:
                if not (0 <= pos[0] < self.model.grid.width and
                        0 <= pos[1] < self.model.grid.height):
                    print(f"Posición inválida en la ruta: {pos}")

        def estoy_cargando(self):
            # Comprueba si el robot está en la misma posición que alguna estación de carga
            contenido_celda_actual = self.model.grid.get_cell_list_contents(self.pos)
            # Create a list of coordinates from the objects in the current cell
            coordenadas_celda_actual = [obj.pos for obj in contenido_celda_actual]
            
            print(f"Robot {self.unique_id} at {self.pos} sees objects at: {coordenadas_celda_actual}")
            
            # Imprimir todos los objetos en la celda actual
            print(f"Objetos en la celda actual: {contenido_celda_actual}")
            
            en_estacion_carga = any(isinstance(obj, EstacionCarga) for obj in contenido_celda_actual)
            
            # Comprobar si hay una instancia de EstacionCarga en la celda
            if en_estacion_carga:
                print(f"Robot {self.unique_id} ha encontrado una estación de carga en la celda {self.pos}")
            
            print(f"Robot {self.unique_id} charging status: {en_estacion_carga}")
            # Retorna True si está en una estación de carga
            return en_estacion_carga and self.carga < 100
        
        def comunicar_ruta(self):
            # Enviar información de ruta a otros robots
             for robot in self.model.schedule.agents:
                 if robot != self and isinstance(robot, RobotLimpieza):
                        robot.recibir_ruta(self.ruta_planeada, self)
        

        def recibir_ruta(self, ruta_otro_robot, otro_robot):
            # Detectar colisión y negociar una nueva ruta si es necesario
            if self.detectar_colision(ruta_otro_robot):
               self.resolver_conflicto(otro_robot)

        def resolver_conflicto(self, otro_robot):
            if self.contador_replanificaciones < self.LIMITE_REPLANIFICACIONES:
                # Lógica actual para ceder o replanificar
                if self.debe_ceder(otro_robot):
                    self.replanificar_ruta()
                else:
                    otro_robot.replanificar_ruta()
                self.contador_replanificaciones += 1
            else:
                # Acción alternativa: esperar o cambiar ruta
                self.esperar_o_cambiar_ruta()
                self.contador_replanificaciones = 0
        def esperar_o_cambiar_ruta(self):
            # Ejemplo: el robot podría esperar un tiempo antes de replanificar
            self.esperar()
            # O buscar una ruta completamente nueva
            self.planificar_ruta_nueva()
        
        def replanificar_ruta(self):
            # Decidir cuál ruta necesita ser replanificada
            if self.necesita_cargar:
                # Si el robot necesita cargar, planifica ruta a la estación de carga
                estacion_cercana = self.encontrar_estacion_carga_mas_cercana()
                if estacion_cercana:
                    self.ruta_planeada = self.algoritmo_a_estrella(self.pos, estacion_cercana.pos)
            else:
                # Si el robot está limpiando, planifica ruta a celda sucia más cercana
                celda_objetivo = self.encontrar_celda_sucia_mas_cercana()
                if celda_objetivo:
                    self.ruta_planeada = self.algoritmo_a_estrella(self.pos, celda_objetivo.pos)
        
        def esperar(self):
            self.contador_espera += 1
            if self.contador_espera >= RobotLimpieza.TIEMPO_ESPERA:
                # Lógica para reanudar actividades después de esperar
                self.contador_espera = 0
                self.replanificar_ruta()
            else:
                # Continúa esperando
                pass

        def detectar_colision(self, ruta_otro_robot):
            # Simple chequeo de colisión
            return any(paso in ruta_otro_robot for paso in self.ruta_planeada)

        def ir_a_estacion_carga(self):
            # Implementar la lógica para ir a la estación de carga más cercana
            estacion_mas_cercana = self.encontrar_estacion_carga_mas_cercana()
            if estacion_mas_cercana:
                self.ruta_planeada = self.planificar_ruta_a_estacion(estacion_mas_cercana.pos)
                # Mover el robot hacia la primera posición en la ruta planeada
                # Suponiendo que tienes una función para mover al robot
                self.mover_a_siguiente_posicion_en_ruta()

        def mover_a_siguiente_posicion_en_ruta(self):
            # Mueve el robot a la siguiente posición en su ruta planeada
            if self.ruta_planeada:
                self.sig_pos = self.ruta_planeada.pop(0)  # Obtiene y elimina el primer elemento de la lista
                # Comprobar si self.sig_pos es una posición válida en la cuadrícula
                if (0 <= self.sig_pos[0] < self.model.grid.width and
                    0 <= self.sig_pos[1] < self.model.grid.height):
                    self.model.grid.move_agent(self, self.sig_pos)
                    # Reducir la batería por movimiento
                    self.carga -= 1
                else:
                    print(f"Posición inválida: {self.sig_pos}")


        def encontrar_estacion_carga_mas_cercana(self):
            # Simplificando: suponemos que hay una lista de estaciones en el modelo
            min_distancia = float('inf')
            estacion_cercana = None
            for estacion in self.model.estaciones_carga:
                distancia = self.distancia_hasta(estacion.pos)
                if distancia < min_distancia:
                    min_distancia = distancia
                    estacion_cercana = estacion
            return estacion_cercana

        def encontrar_celda_sucia_mas_cercana(self):
            # Crear una cola y agregar la posición actual del robot
            cola = deque([self.pos])
            # Crear un conjunto para almacenar las posiciones visitadas
            visitados = set([self.pos])

            while cola:
                pos = cola.popleft()
                contenido_celda = self.model.grid.get_cell_list_contents(pos)

                # Comprobar si la celda está sucia
                for obj in contenido_celda:
                    if isinstance(obj, Celda) and obj.sucia:
                        return pos

                # Agregar las posiciones adyacentes a la cola (incluyendo las diagonales)
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    nueva_pos = (pos[0] + dx, pos[1] + dy)
                    if (0 <= nueva_pos[0] < self.model.grid.width and
                        0 <= nueva_pos[1] < self.model.grid.height and
                        nueva_pos not in visitados):
                        cola.append(nueva_pos)
                        visitados.add(nueva_pos)

            # No hay celdas sucias en la cuadrícula
            return None


        def distancia_hasta(self, destino):
            # Implementación simple de la distancia Manhattan
            (x1, y1) = self.pos
            (x2, y2) = destino
            return abs(x1 - x2) + abs(y1 - y2)
           
        def actualizar_ruta(self):
            # Comprobar si la ruta actual sigue siendo válida
            if not self.ruta_es_valida():
                self.replanificar_ruta()
        
        def ruta_es_valida(self):
            # Ejemplo de comprobación de validez de la ruta
            # Esto es solo un esquema y debería ser adaptado según las necesidades específicas del modelo
            if self.ruta_planeada:
                # Comprobar si el objetivo sigue siendo relevante (por ejemplo, si es una celda sucia, verificar que siga sucia)
                ultimo_destino = self.ruta_planeada[-1]
                contenido_ultimo_destino = self.model.grid.get_cell_list_contents([ultimo_destino])
                if any(isinstance(obj, Celda) and obj.sucia for obj in contenido_ultimo_destino):
                    return True
                else:
                    return False
            else:
                # Si no hay ruta planeada, no es válida
                return False

        def planificar_ruta_limpieza(self):
            # Encuentra la celda sucia más cercana
            celda_mas_cercana = self.encontrar_celda_sucia_mas_cercana()

            # Si no hay celdas sucias, no hay necesidad de planificar una ruta
            if celda_mas_cercana is None:
                return
            # Planifica una ruta hasta la celda sucia más cercana utilizando A*

        
            self.ruta_planeada = self.algoritmo_a_estrella(self.pos, celda_mas_cercana.pos)

        def algoritmo_a_estrella(self, inicio, destino):
            frontera = PriorityQueue()
            frontera.put((0, inicio))
            camino = {inicio: None}
            costo_hasta_ahora = {inicio: 0}

            while not frontera.empty():
                _, actual = frontera.get()

                if actual == destino:
                    break

                for siguiente in self.obtener_vecinos(actual):
                    nuevo_costo = costo_hasta_ahora[actual] + 1  # Assuming a uniform cost
                    if siguiente not in costo_hasta_ahora or nuevo_costo < costo_hasta_ahora[siguiente]:
                        costo_hasta_ahora[siguiente] = nuevo_costo
                        prioridad = nuevo_costo + self.heuristica(siguiente, destino)
                        frontera.put((prioridad, siguiente))
                        camino[siguiente] = actual

            return self.reconstruir_camino(camino, inicio, destino)

            
        def planificar_ruta_a_estacion(self, destino):
            inicio = self.pos
            self.ruta_planeada = self.algoritmo_a_estrella(inicio, destino)



        def obtener_vecinos(self, pos, evitar_obstaculos=True):
            vecinos = []
            direcciones = [(1, 0), (-1, 0), (0, 1), (0, -1)]  # Movimientos posibles
            for dx, dy in direcciones:
                x, y = pos[0] + dx, pos[1] + dy
                if 0 <= x < self.model.grid.width and 0 <= y < self.model.grid.height:
                    if evitar_obstaculos and not self.model.grid.is_cell_empty((x, y)):
                        continue
                    vecinos.append((x, y))
            return vecinos


        def heuristica(self, a, b):
            (x1, y1) = a
            (x2, y2) = b
            return abs(x1 - x2) + abs(y1 - y2)

        def reconstruir_camino(self, camino, inicio, destino):
            ruta = []
            actual = destino
            while actual != inicio:
                if actual not in camino:  # Safety check for unreachable destination
                    return []  # Or raise an exception or handle it as per the simulation's requirement
                ruta.append(actual)
                actual = camino[actual]
            ruta.reverse()  # The path is reconstructed backwards, so we need to reverse it at the end
            return ruta

       


class Habitacion(Model):
      def __init__(self, M: int, N: int,
                   num_agentes: int = 5,
                   porc_celdas_sucias: float = 0.6,
                   porc_muebles: float = 0.1,
                   modo_pos_inicial: str = 'Fija',
                    ):
          super().__init__()
          self.current_id = 0
          self.estaciones_carga = []
          self.num_agentes = num_agentes
          self.porc_celdas_sucias = porc_celdas_sucias
          self.porc_muebles = porc_muebles

          self.grid = MultiGrid(M, N, False)
          self.schedule = SimultaneousActivation(self)

          posiciones_disponibles = [pos for _, pos in self.grid.coord_iter()]
        # Posicionamiento de muebles
          num_muebles = int(M * N * porc_muebles)
          posiciones_muebles = self.random.sample(posiciones_disponibles, k=num_muebles)
          for id, pos in enumerate(posiciones_muebles):
              mueble = Mueble(int(f"{num_agentes}0{id}") + 1, self)
              self.grid.place_agent(mueble, pos)
              posiciones_disponibles.remove(pos)

                # Posicionamiento de celdas sucias
          self.num_celdas_sucias = int(M * N * porc_celdas_sucias)
          posiciones_celdas_sucias = self.random.sample(
          posiciones_disponibles, k=self.num_celdas_sucias)

          for id, pos in enumerate(posiciones_disponibles):
              suciedad = pos in posiciones_celdas_sucias
              celda = Celda(int(f"{num_agentes}{id}") + 1, self, suciedad)
              self.grid.place_agent(celda, pos)

                # Posicionamiento de agentes robot
          if modo_pos_inicial == 'Aleatoria':
             pos_inicial_robots = self.random.sample(posiciones_disponibles, k=num_agentes)
          else:  # 'Fija'
               pos_inicial_robots = [(1, 1)] * num_agentes

          for id in range(num_agentes):
              robot = RobotLimpieza(id, self)
              self.grid.place_agent(robot, pos_inicial_robots[id])
              self.schedule.add(robot)       

          self.datacollector = DataCollector(
               model_reporters={"Grid": Habitacion.get_grid, "Cargas": Habitacion.get_cargas,
                               "CeldasSucias": Habitacion.get_sucias},
          )
          self.agregar_estaciones_carga()
      
      def is_cell_empty(self, pos):
          """
                Comprueba si una celda está vacía o contiene ciertos tipos de agentes.
                :param pos: Tupla de posición (x, y).
                :return: True si la celda está "vacía" para los propósitos del robot.
                """
          cell_contents = self.grid.get_cell_list_contents(pos)
          if not cell_contents:
             return True  # La celda está literalmente vacía

                # Considera la celda "vacía" si solo contiene agentes que no bloquean el movimiento
          for agent in cell_contents:
              if isinstance(agent, (Mueble, RobotLimpieza)):
                 return False  # La celda está bloqueada

          return True  # La celda contiene agentes, pero son del tipo no bloqueante
      def next_id(self):
            """ Returns the next available ID for a new agent. """
            self.current_id += 1
            return self.current_id
      def agregar_estaciones_carga(self):
            # Determinar el número de estaciones de carga necesarias
            num_estaciones = (self.grid.width * self.grid.height) // 4

            # Añadir estaciones de carga
            for _ in range(num_estaciones):
                pos = self.seleccionar_posicion_para_estacion()
                estacion = EstacionCarga(self.next_id(), self)
                self.grid.place_agent(estacion, pos)
                self.estaciones_carga.append(estacion)
                print(f"Estación de carga agregada en la posición {pos}")

            # Verificar que cada estación de carga se ha agregado correctamente
            for estacion in self.estaciones_carga:
                celda = self.grid.get_cell_list_contents([estacion.pos])
                assert any(isinstance(obj, EstacionCarga) for obj in celda), f"La celda {estacion.pos} no contiene una estación de carga"
            print("Todas las estaciones de carga se han agregado correctamente")

      def seleccionar_posicion_para_estacion(self):
                    # Implementar la lógica para seleccionar una posición válida
            posiciones_disponibles = [pos[1] for pos in self.grid.coord_iter()]
                    # Eliminar posiciones ocupadas por muebles o agentes
            posiciones_disponibles = [pos for pos in posiciones_disponibles if self.is_cell_empty(pos)]
                    # Escoger una posición aleatoria de las disponibles
            return self.random.choice(posiciones_disponibles)
      def step(self):
          self.datacollector.collect(self)
          self.schedule.step()
      def todoLimpio(self):
            for (content, x, y) in self.grid.coord_iter():
                    for obj in content:
                        if isinstance(obj, Celda) and obj.sucia:
                            return False
            return True
      @staticmethod
      def get_grid(model: Model) -> np.ndarray:
            grid = np.zeros((model.grid.width, model.grid.height))
            for cell in model.grid.coord_iter():
                cell_content, pos = cell
                x, y = pos
                for obj in cell_content:
                    if isinstance(obj, RobotLimpieza):
                       grid[x][y] = 2   
                    elif isinstance(obj, Celda):
                         grid[x][y] = int(obj.sucia)
            return grid
      @staticmethod      
      def get_cargas(model: Model):
           return [(agent.unique_id, agent.carga) for agent in model.schedule.agents]
      @staticmethod
      def get_sucias(model: Model) -> int:
            sum_sucias = 0
            for cell in model.grid.coord_iter():
                cell_content, pos = cell
                for obj in cell_content:
                    if isinstance(obj, Celda) and obj.sucia:
                       sum_sucias += 1
            return sum_sucias / model.num_celdas_sucias
      def get_movimientos(agent: Agent) -> dict:
            if isinstance(agent, RobotLimpieza):
                return {agent.unique_id: agent.movimientos}
                        # else:
                        #    return 0   
                       
                   

            

            

        