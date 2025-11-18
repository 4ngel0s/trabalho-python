    import flet as ft
    import sqlite3
    from datetime import datetime

    DB_FILE = "logmanutencion.db"

    # ============================
    # BANCO DE DADOS (com migração de colunas)
    # ============================

    def criar_banco():
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Cria a tabela com as colunas mais completas (se não existir)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS encomendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                codigo TEXT NOT NULL,
                descricao TEXT NOT NULL,
                quantidade INTEGER NOT NULL,
                status TEXT NOT NULL,
                forma_saida TEXT,
                data_entrada TEXT,
                hora_entrada TEXT
            )
        """)
        conn.commit()

        # Função auxiliar para checar se uma coluna existe na tabela
        def coluna_existe(nome_coluna: str) -> bool:
            cursor.execute("PRAGMA table_info(encomendas)")
            cols = [row[1] for row in cursor.fetchall()]  # row[1] é o nome da coluna
            return nome_coluna in cols

        # Se por algum motivo o banco veio de versão antiga sem as colunas, adiciona-as
        if not coluna_existe("data_entrada"):
            cursor.execute("ALTER TABLE encomendas ADD COLUMN data_entrada TEXT")
        if not coluna_existe("hora_entrada"):
            cursor.execute("ALTER TABLE encomendas ADD COLUMN hora_entrada TEXT")

        conn.commit()
        conn.close()


    def inserir_encomenda(codigo, descricao, quantidade):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        data = datetime.now().strftime("%Y-%m-%d")
        hora = datetime.now().strftime("%H:%M:%S")

        cursor.execute("""
            INSERT INTO encomendas 
            (codigo, descricao, quantidade, status, data_entrada, hora_entrada)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (codigo, descricao, quantidade, "Armazenado", data, hora))

        conn.commit()
        conn.close()


    def atualizar_saida(codigo, forma_saida):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE encomendas
            SET status = ?, forma_saida = ?
            WHERE codigo = ?
        """, ("Retirado", forma_saida, codigo))
        conn.commit()
        conn.close()


    def limpar_estoque():
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM encomendas")
        conn.commit()
        conn.close()


    def carregar_estoque():
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT codigo, descricao, quantidade, status, forma_saida, 
                COALESCE(data_entrada, ''), COALESCE(hora_entrada, '')
            FROM encomendas
        """)
        dados = cursor.fetchall()
        conn.close()
        return dados


    # ============================
    # APLICATIVO FLET
    # ============================

    def main(page: ft.Page):
        page.title = "LogManutencion"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.adaptive = True
        page.scroll = "auto"
        page.padding = 20

        COR_PRIMARIA = "#E65100"
        COR_SECUNDARIA = "#FF8A00"
        COR_DESTAQUE = "#D84315"

        # Atualiza tabela
        def atualizar_tabela():
            tabela.rows.clear()
            for c, d, q, s, f, data, hora in carregar_estoque():
                tabela.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(c))),
                            ft.DataCell(ft.Text(str(d))),
                            ft.DataCell(ft.Text(str(q))),
                            ft.DataCell(ft.Text(str(s))),
                            ft.DataCell(ft.Text(str(f) if f else "-")),
                            ft.DataCell(ft.Text(str(data) if data else "-")),
                            ft.DataCell(ft.Text(str(hora) if hora else "-")),
                        ]
                    )
                )
            page.update()

        # Funções
        def adicionar_item(e):
            if not (codigo.value and descricao.value and quantidade.value):
                page.snack_bar = ft.SnackBar(ft.Text("Preencha todos os campos!"), bgcolor=COR_DESTAQUE)
                page.snack_bar.open = True
                page.update()
                return

            try:
                q = int(quantidade.value)
            except ValueError:
                page.snack_bar = ft.SnackBar(ft.Text("Quantidade inválida! Use apenas números."), bgcolor=COR_DESTAQUE)
                page.snack_bar.open = True
                page.update()
                return

            inserir_encomenda(codigo.value, descricao.value, q)
            codigo.value = descricao.value = quantidade.value = ""
            atualizar_tabela()

        def registrar_saida(e):
            if not codigo_saida.value or not forma_envio.value:
                page.snack_bar = ft.SnackBar(ft.Text("Informe o código e a forma de retirada!"), bgcolor=COR_DESTAQUE)
                page.snack_bar.open = True
                page.update()
                return

            atualizar_saida(codigo_saida.value, forma_envio.value)
            atualizar_tabela()

        def reiniciar_estoque(e):
            limpar_estoque()
            atualizar_tabela()
            page.snack_bar = ft.SnackBar(ft.Text("Estoque limpo com sucesso!"), bgcolor="green")
            page.snack_bar.open = True
            page.update()

        # Campos
        codigo = ft.TextField(label="Código", border_color=COR_PRIMARIA)
        descricao = ft.TextField(label="Descrição", border_color=COR_PRIMARIA)
        quantidade = ft.TextField(label="Quantidade", keyboard_type=ft.KeyboardType.NUMBER, border_color=COR_PRIMARIA)

        codigo_saida = ft.TextField(label="Código da Encomenda", border_color=COR_PRIMARIA)

        forma_envio = ft.Dropdown(
            label="Forma de Retirada",
            border_color=COR_PRIMARIA,
            options=[
                ft.dropdown.Option("99"),
                ft.dropdown.Option("Uber"),
                ft.dropdown.Option("Lalamove"),
                ft.dropdown.Option("Transportadora"),
                ft.dropdown.Option("Retirada pelo Cliente")
            ]
        )

        # Botões
        btn_add = ft.ElevatedButton(
            "Adicionar ao Estoque",
            on_click=adicionar_item,
            bgcolor=COR_SECUNDARIA,
            color="white",
            width=250,
            height=45
        )

        btn_saida = ft.ElevatedButton(
            "Registrar Saída",
            on_click=registrar_saida,
            bgcolor=COR_DESTAQUE,
            color="white",
            width=250,
            height=45
        )

        btn_reset = ft.ElevatedButton(
            "Limpar Estoque",
            on_click=reiniciar_estoque,
            bgcolor="#B71C1C",
            color="white",
            width=250,
            height=45
        )

        # Tabela
        tabela = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Código")),
                ft.DataColumn(ft.Text("Descrição")),
                ft.DataColumn(ft.Text("Qtd")),
                ft.DataColumn(ft.Text("Status")),
                ft.DataColumn(ft.Text("Saída")),
                ft.DataColumn(ft.Text("Data Entrada")),
                ft.DataColumn(ft.Text("Hora Entrada")),
            ],
            rows=[]
        )

        # Tabs
        page.add(
            ft.Tabs(
                expand=True,
                tabs=[
                    ft.Tab(
                        text="Recebimento",
                        icon=ft.Icon(name="add_box"),
                        content=ft.Column([
                            ft.Text("Cadastro de Encomendas", size=20, weight="bold", color=COR_PRIMARIA),
                            codigo,
                            descricao,
                            quantidade,
                            btn_add
                        ], spacing=15)
                    ),
                    ft.Tab(
                        text="Saída",
                        icon=ft.Icon(name="local_shipping"),
                        content=ft.Column([
                            ft.Text("Registrar Saída", size=20, weight="bold", color=COR_PRIMARIA),
                            codigo_saida,
                            forma_envio,
                            btn_saida
                        ], spacing=15)
                    ),
                    ft.Tab(
                        text="Estoque",
                        icon=ft.Icon(name="inventory_2"),
                        content=ft.Column([
                            ft.Text("Itens no Estoque", size=20, weight="bold", color=COR_PRIMARIA),
                            ft.Container(
                                tabela,
                                expand=True,
                                bgcolor="white",
                                padding=10,
                                border_radius=10,
                                height=420
                            ),
                            btn_reset
                        ], spacing=15)
                    )
                ]
            )
        )

        atualizar_tabela()


    if __name__ == "__main__":
        criar_banco()
        ft.app(target=main)
