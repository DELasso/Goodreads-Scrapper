from Scrapper import *
import json
import networkx as nx
import os


class Graph:
    def __init__(self, directed=True):
        self.adj_list = {}
        self.directed = directed

    def get_neighbors(self, node_label):
        if node_label in self.adj_list:
            return self.adj_list[node_label]['neighbors']
        return []

    def add_vertex(self, node_label, node_type=None, **attributes):
        if node_label not in self.adj_list:
            self.adj_list[node_label] = {'type': node_type, 'neighbors': []}

            if node_type == 'author':
                self.adj_list[node_label]['name'] = node_label

            for key, value in attributes.items():
                self.adj_list[node_label][key] = value

    def add_edge(self, v1, v2):
        if v1 not in self.adj_list:
            self.add_vertex(v1)
        if v2 not in self.adj_list:
            self.add_vertex(v2)
        self.adj_list[v1]['neighbors'].append(v2)
        if not self.directed:
            self.adj_list[v2]['neighbors'].append(v1)

    def find_author_books(self, author_name):
        author_books = []

        for node, attr in self.adj_list.items():
            if attr['type'] == 'author' and attr['name'] == author_name:
                author_books_data = []
                for book in attr['neighbors']:
                    book_data = self.adj_list[book]
                    release_date = book_data['release_date']
                    author_books_data.append((book, release_date))

                author_books_data.sort(key=lambda x: (x[1][2], x[1][0], x[1][1]))

                author_books.extend([f"{book} ({release_date[2]})" for book, release_date in author_books_data])

        if not author_books:
            return None

        return author_books

    def recommend_books(self, book_title, genre_name, decade, n=5):
        recommended_books = []

        if book_title not in self.adj_list or self.adj_list[book_title]['type'] != 'book':
            return "El libro de referencia no existe en el grafo o no es un libro."

        reference_book_data = self.adj_list[book_title]
        _reference_release_date = reference_book_data['release_date']

        for node, attr in self.adj_list.items():
            if attr['type'] == 'book':
                if 'genres' in attr and genre_name in attr['genres']:
                    release_date = attr['release_date']

                    if (release_date[2] // 10) * 10 == (decade // 10) * 10:
                        recommended_books.append((node, release_date))

        recommended_books.sort(key=lambda x: (x[1][2], x[1][0], x[1][1]))

        recommended_books = recommended_books[:n]

        if not recommended_books:
            return f"No se encontraron libros del género {genre_name} y década {decade} para recomendar."

        result = f"Libros recomendados para el libro {book_title} del género {genre_name} y década {decade}:\n"
        for book, release_date in recommended_books:
            result += f"{book} ({release_date[2]})\n"

        return result

    def find_authors_by_genre(self, genre_name):
        author_books_count = {}

        for node, attr in self.adj_list.items():
            if attr['type'] == 'author':
                author_books = [book for book in attr['neighbors'] if self.adj_list[book]['type'] == 'book']
                genre_books = [book for book in author_books if
                               'genres' in self.adj_list[book] and genre_name in self.adj_list[book]['genres']]
                author_books_count[node] = len(genre_books)
        sorted_authors = sorted(author_books_count.items(), key=lambda x: x[1], reverse=True)

        return sorted_authors

    def recommend_books_by_score_and_genre(self, min_score, genre_names, n=5):
        recommended_books = []

        for node, attr in self.adj_list.items():
            if attr['type'] == 'book' and 'score' in attr and attr['score'] >= min_score and any(
                    genre in attr['genres'] for genre in genre_names):
                recommended_books.append((node, attr.get('release_date'), attr.get('score', 0)))

        recommended_books.sort(key=lambda x: x[2], reverse=True)

        recommended_books = recommended_books[:n]

        if not recommended_books:
            return f"No se encontraron libros con un puntaje mayor a {min_score} en los géneros especificados."

        result = f"Libros recomendados con puntaje mayor a {min_score} en los géneros {', '.join(genre_names)} (ordenados por puntaje):\n"
        for book, release_date, score in recommended_books:
            result += f"{book} ({release_date[2]}) - Puntaje: {score}\n"

        return result

    def recommend_list_shopping(self, money, genre_names):
        recommended_books = []

        for node, attr in self.adj_list.items():
            if attr['type'] == 'book' and 'genres' in attr and any(genre in attr['genres'] for genre in genre_names) and \
                    attr['price'] <= money:
                recommended_books.append((node, attr['release_date'], attr['price']))

        recommended_books.sort(key=lambda x: x[2])

        total_cost = 0
        selected_books = []
        for book, release_date, price in recommended_books:
            if total_cost + price <= money:
                total_cost += price
                selected_books.append((book, release_date))

        if not selected_books:
            return f"No se encontraron libros en los géneros especificados dentro del presupuesto de {money}."

        result = f"Mejor lista de compras para obtener el mayor número de libros en los géneros " \
                 f"{', '.join(genre_names)} " \
                 f"dentro del presupuesto de {money}:\n"
        for book, release_date in selected_books:
            result += f"{book} ({release_date[2]}) - Precio: {self.adj_list[book]['price']}\n"

        return result

    def relation_V1_V2(self, v1, v2):
        if v1 not in self.adj_list or v2 not in self.adj_list:
            return "Al menos uno de los nodos no existe en el grafo"

        if v2 in self.adj_list[v1]['neighbors']:
            return f"{v1} y {v2} están directamente relacionados en el grafo"
        visited = set()
        queue = [(v1, [])]
        while queue:
            current_node, path = queue.pop(0)
            if current_node == v2:
                return f"Se encontró una ruta de relación indirecta entre {v1} y {v2}: {' -> '.join(path + [current_node])}"

            visited.add(current_node)
            neighbors = self.get_neighbors(current_node)

            for neighbor in neighbors:
                if neighbor not in visited:
                    queue.append((neighbor, path + [current_node]))

        return f"No se encontró una relación entre {v1} y {v2} en el grafo"

    def get_num_nodes(self):
        return len(self.adj_list)

    def get_num_edges(self):
        total_edges = sum(len(neighbors) for neighbors in self.adj_list.values())
        if not self.directed:
            total_edges //= 2
        return total_edges


with open("all_books.json", "r") as json_file:
    data = json.load(json_file)

book_list = []
for book_data in data:
    title = book_data["title"]
    author = book_data["author"]
    release_date = book_data["release_date"]
    price = book_data["price"]
    score = book_data["score"]
    genres = book_data["genres"]
    book = Book(title, author, release_date, price, score, genres)
    book_list.append(book)

g = Graph()

for book in book_list:
    g.add_vertex(book.title, node_type='book', author=book.author, release_date=book.release_date, price=book.price,
                 score=book.score, genres=book.genres)
    g.add_vertex(book.author, node_type='author')
    g.add_edge(book.title, book.author)
    g.add_edge(book.author, book.title)


# Agregar nodos y relaciones
g.add_vertex("Book1", node_type='book', author='Author1')
g.add_vertex("Book2", node_type='book', author='Author2')
g.add_vertex("Author1", node_type='author')
g.add_vertex("Author2", node_type='author')

g.add_edge("Book1", "Author1")
g.add_edge("Book2", "Author2")
g.add_edge("Author1", "Book1")
g.add_edge("Author2", "Book2")
g.add_edge("Author1", "Author2")

# Algunos ejemplos de llamadas a relation_V1_V2
print(g.relation_V1_V2("Book1", "Author1"))
print(g.relation_V1_V2("Book1", "Author2"))
print(g.relation_V1_V2("Author1", "Author2"))
print(g.relation_V1_V2("Book2", "Author1"))

num_nodes = g.get_num_nodes()
print(f"La longitud de los nodos en el grafo es: {num_nodes}")
num_edges = g.get_num_edges()
print(f"La longitud de las conexiones en el grafo es: {num_edges}")


def save_graph():
    G = nx.Graph()
    for node, attr in g.adj_list.items():
        G.add_node(node, **attr)
        for neighbor in attr['neighbors']:
            G.add_edge(node, neighbor)

    for node in G.nodes:
        attr = G.nodes[node]
        for key, value in attr.items():
            if isinstance(value, (list, type)):
                attr[key] = str(value)

    if os.path.exists("graph.graphml"):
        os.remove("graph.graphml")

    nx.write_graphml(G, "graph.graphml")


def user_menu():
    print("\nBienvenido al grafo de libros de Goodreads!")
    print("Puedes realizar las siguientes acciones:")
    print('''
1. Guardar el grafo en archivo .GRAPHML.
2. Recomendar lista de compras.
3. Listar a los autores del género X.
4. Recomendar libros de puntaje mayor a X.
5. Encontrar los libros de un autor.
6. Recomendar N libros del mismo género y década que el libro X.
7. Conocer la relación directa o indirecta de dos nodos v1 y v2.                                                    
8. Salir.
    ''')
    while True:
        option = input("\nIngresa tu opción: ")
        if option == "1":
            save_graph()
            print("El grafo se ha guardado correctamente! Puedes verlo en Cytoscape")

        elif option == "2":
            budget = float(input("Ingresa tu presupuesto: "))
            genre_names = input("Ingresa los nombres de los géneros separados por comas: ").split(',')
            print(g.recommend_list_shopping(budget, genre_names))

        elif option == "3":
            genre_name = input("Ingresa el nombre del género que quieres buscar: ")
            authors_by_genre = g.find_authors_by_genre(genre_name)
            if authors_by_genre:
                print(f"Autores del género {genre_name} ordenados por la cantidad de libros escritos:")
                for author, count in authors_by_genre:
                    print(f"{author}: {count} libros")
            else:
                print(f"No se encontraron autores para el género {genre_name}")

        elif option == "4":
            min_score = int(input("Ingresa el puntaje mínimo para la recomendación: "))
            genre_names = input("Ingresa los nombres de los géneros separados por comas: ").split(',')
            n = int(input("Ingresa el número de libros a recomendar: "))
            print(g.recommend_books_by_score_and_genre(min_score, genre_names, n))

        elif option == "5":
            author_name = input("Ingresa el nombre del autor que quieres buscar: ")
            author_books = g.find_author_books(author_name)
            if author_books:
                print(f"Libros del autor {author_name}: {', '.join(author_books)}")
            else:
                print(f"No se encontraron libros para el autor {author_name}")

        elif option == "6":
            book_title = input("Ingresa el título del libro de referencia: ")
            genre_name = input("Ingresa el nombre del género para la recomendación: ")
            decade = int(input("Ingresa la década para la recomendación (por ejemplo, 1990): "))
            n = int(input("Ingresa el número de libros a recomendar: "))
            print(g.recommend_books(book_title, genre_name, decade, n))

        elif option == "7":
            v1 = input("Ingresa el primer nodo (v1): ")
            v2 = input("Ingresa el segundo nodo (v2): ")
            print(g.relation_V1_V2(v1, v2))

        elif option == "8":
            break
        else:
            print("Ingresa un valor válido!")


user_menu()
