import os
import sqlite3
from datetime import datetime
from flask import Flask, request, redirect, url_for, render_template_string

app = Flask(__name__)
app.secret_key = "stockweb_secret_key"
DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), "database.db")

# ==========================================
# BANCO DE DADOS E LÓGICA DE NEGÓCIO
# ==========================================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                quantidade INTEGER NOT NULL,
                data_validade TEXT NOT NULL
            )
        """)
        conn.commit()

def calcular_status(data_validade_str):
    try:
        data_validade = datetime.strptime(data_validade_str, "%Y-%m-%d").date()
        hoje = datetime.now().date()
        dias_restantes = (data_validade - hoje).days

        if dias_restantes < 0:
            return {"label": "Vencido", "classe": "status-vencido"}
        elif 0 <= dias_restantes <= 3:
            return {"label": "Próximo do vencimento", "classe": "status-proximo"}
        else:
            return {"label": "Válido", "classe": "status-valido"}
    except ValueError:
        return {"label": "Inválido", "classe": "bg-secondary text-white"}

# ==========================================
# TEMPLATE GLOBAL (HTML + CSS TOTALMENTE RESPONSIVO)
# ==========================================

BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StockWeb</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.2/font/bootstrap-icons.css">
    <style>
        body { background-color: #f0f2f5; font-family: system-ui, -apple-system, sans-serif; overflow-x: hidden; }
        .row-container { min-height: 100vh; }
        
        /* Sidebar Fiel ao Protótipo - Layout PC */
        .sidebar { background-color: #062c65; min-height: 100vh; color: white; padding: 25px 15px; }
        .sidebar h3 { font-size: 1.4rem; font-weight: 700; margin-bottom: 30px; padding-left: 10px; letter-spacing: -0.5px; }
        .sidebar .nav-link { color: #b3c5dc; border-radius: 8px; margin-bottom: 10px; padding: 12px 18px; font-weight: 500; text-decoration: none; display: block; transition: all 0.2s ease; }
        .sidebar .nav-link:hover { color: white; background-color: rgba(255, 255, 255, 0.05); }
        .sidebar .nav-link.active { background-color: #1b52a4; color: white; font-weight: 500; }
        
        /* Área de Conteúdo */
        .main-container { background-color: #ffffff; border-radius: 16px; border: 1px solid #e1e4e8; min-height: calc(100vh - 40px); margin: 20px 0; padding: 40px !important; display: flex; flex-direction: column; justify-content: space-between; }
        .top-header-title { font-size: 1.65rem; font-weight: 700; color: #111111; }
        .top-header-sub { color: #666666; font-size: 0.95rem; margin-top: 4px; }
        .brand-badge { color: #062c65; font-weight: 600; font-size: 0.9rem; }
        .brand-badge i { font-size: 1.1rem; vertical-align: middle; margin-right: 4px; }
        
        /* Bloco de Formulário Interno */
        .card-form { border: 1px solid #e1e4e8; border-radius: 8px; background-color: #ffffff; padding: 25px; margin-top: 25px; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }
        .card-form-title { font-size: 1rem; font-weight: 700; color: #111111; margin-bottom: 20px; }
        .form-label { font-weight: 500; color: #111111; font-size: 0.9rem; margin-bottom: 8px; }
        .form-control { border: 1px solid #cccccc; border-radius: 6px; padding: 10px 14px; font-size: 0.92rem; background-color: #ffffff; color: #333333; }
        .form-control::placeholder { color: #aaaaaa; }
        .form-control:focus { border-color: #1b52a4; box-shadow: none; }
        
        /* Botões */
        .btn-salvar { background-color: #1459cb; color: white; border: none; padding: 10px 20px; font-weight: 500; border-radius: 6px; font-size: 0.9rem; }
        .btn-salvar:hover { background-color: #0f46a3; color: white; }
        .btn-limpar { background-color: #7a828a; color: white; border: none; padding: 10px 20px; font-weight: 500; border-radius: 6px; font-size: 0.9rem; }
        .btn-limpar:hover { background-color: #626970; color: white; }
        .btn-novo { background-color: #1459cb; color: white; border: none; padding: 10px 18px; font-weight: 500; border-radius: 6px; font-size: 0.9rem; }
        .btn-novo:hover { background-color: #0f46a3; color: white; }
        
        /* Tabela */
        .table { margin-top: 15px; border-collapse: separate; border-spacing: 0; width: 100%; }
        .table thead th { background-color: #f4f6f8; color: #333333; font-weight: 600; font-size: 0.9rem; padding: 14px; border-bottom: 1px solid #e1e4e8; border-top: 1px solid #e1e4e8; }
        .table tbody td { padding: 14px; font-size: 0.92rem; color: #333333; border-bottom: 1px solid #e1e4e8; vertical-align: middle; }
        
        /* Badges de Status */
        .status-badge { padding: 4px 14px; border-radius: 12px; font-size: 0.82rem; font-weight: 500; display: inline-block; }
        .status-proximo { background-color: #fef3d6; color: #b27b10; }
        .status-valido { background-color: #e3f7ed; color: #218353; }
        .status-vencido { background-color: #fde7e9; color: #ca333f; }
        
        /* Botões de Ação */
        .btn-action-edit { background-color: #1459cb; color: white; width: 34px; height: 34px; padding: 0; display: inline-flex; align-items: center; justify-content: center; border-radius: 6px; border: none; font-size: 0.9rem; }
        .btn-action-edit:hover { background-color: #0f46a3; color: white; }
        .btn-action-delete { background-color: #d92534; color: white; width: 34px; height: 34px; padding: 0; display: inline-flex; align-items: center; justify-content: center; border-radius: 6px; border: none; font-size: 0.9rem; margin-left: 4px; }
        .btn-action-delete:hover { background-color: #b31d2a; color: white; }
        
        /* Rodapé Sincronizado */
        .footer-menu { font-size: 0.85rem; color: #333333; margin-top: auto; padding-top: 30px; }
        .footer-menu a { text-decoration: none; color: #666663; margin: 0 4px; font-weight: 500; }
        .footer-menu a.active { color: #1459cb; font-weight: 600; }

        /* ==================================================================
           ADAPTAÇÃO ADICIONADA PARA CELULAR (RESPONSIVIDADE - MAX 768px)
           ================================================================== */
        @media (max-width: 768px) {
            .row-container { flex-direction: column !important; }
            
            /* Transforma a sidebar em uma barra superior compacta */
            .sidebar { 
                min-height: auto !important; 
                width: 100% !important; 
                padding: 15px !important; 
                text-align: center;
            }
            .sidebar h3 { margin-bottom: 15px; padding-left: 0; font-size: 1.25rem; }
            
            /* Coloca os links do menu lado a lado horizontalmente */
            .sidebar .nav { 
                flex-direction: row !important; 
                justify-content: center !important; 
                gap: 10px; 
            }
            .sidebar .nav-link { 
                margin-bottom: 0 !important; 
                padding: 8px 16px !important; 
                font-size: 0.9rem; 
            }
            
            /* Ajusta a área do conteúdo para ocupar a tela inteira do celular */
            .main-col { width: 100% !important; padding: 10px !important; }
            .main-container { margin: 10px 0 !important; padding: 20px !important; min-height: auto !important; }
            
            /* Ajustes finos nos espaçamentos internos */
            .top-header-title { font-size: 1.35rem; }
            .card-form { padding: 15px; }
            .btn-salvar, .btn-limpar, .btn-novo { width: 100%; margin-bottom: 10px; }
            .mt-4.pt-2 { display: flex; flex-direction: column; }
        }
    </style>
</head>
<body>
<div class="container-fluid p-0">
    <div class="row g-0 row-container">
        <div class="col-md-2 sidebar">
            <h3>StockWeb</h3>
            <div class="nav flex-column">
                <a href="/cadastro" class="nav-link {% if active_page == 'cadastro' %}active{% endif %}">
                    <i class="bi bi-file-earmark-plus me-2"></i> Cadastro
                </a>
                <a href="/estoque" class="nav-link {% if active_page == 'estoque' %}active{% endif %}">
                    <i class="bi bi-box-seam me-2"></i> Estoque
                </a>
            </div>
        </div>
        <div class="col-md-10 px-md-4 main-col d-flex flex-column justify-content-between">
            <div class="main-container d-flex flex-column justify-content-between">
                <div class="w-100">
                    {{ content | safe }}
                </div>
                <div class="footer-menu text-start border-top pt-3 w-100">
                    Menu: 
                    <a href="/cadastro" class="{% if active_page == 'cadastro' %}active{% endif %}">Cadastro</a> | 
                    <a href="/estoque" class="{% if active_page == 'estoque' %}active{% endif %}">Estoque</a>
                </div>
            </div>
        </div>
    </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# ==========================================
# ROTAS E RENDERIZAÇÃO INTERNA
# ==========================================

@app.route("/")
def index():
    return redirect(url_for("cadastro"))

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    produto = None
    edit_id = request.args.get("editar")
    
    if edit_id:
        with get_db_connection() as conn:
            produto = conn.execute("SELECT * FROM produtos WHERE id = ?", (edit_id,)).fetchone()

    if request.method == "POST":
        nome = request.form.get("nome")
        quantidade = request.form.get("quantidade")
        data_validade = request.form.get("data_validade")
        prod_id = request.form.get("prod_id")

        with get_db_connection() as conn:
            if prod_id:
                conn.execute(
                    "UPDATE produtos SET nome = ?, quantidade = ?, data_validade = ? WHERE id = ?",
                    (nome, int(quantidade), data_validade, prod_id)
                )
            else:
                conn.execute(
                    "INSERT INTO produtos (nome, quantidade, data_validade) VALUES (?, ?, ?)",
                    (nome, int(quantidade), data_validade)
                )
            conn.commit()
        return redirect(url_for("estoque"))

    titulo = "Editar Produto" if produto else "Cadastro de Produto"
    subtitulo = "Preencha os dados abaixo para atualizar o produto no estoque." if produto else "Preencha os dados abaixo para cadastrar um novo produto no estoque."
    nome_val = produto["nome"] if produto else ""
    qtd_val = produto["quantidade"] if produto else ""
    data_val = produto["data_validade"] if produto else ""
    id_hidden = f'<input type="hidden" name="prod_id" value="{produto["id"]}">' if produto else ""

    cadastro_html = f"""
    <div class="d-flex justify-content-between align-items-start mb-2">
        <div>
            <h2 class="top-header-title m-0">{titulo}</h2>
            <p class="top-header-sub m-0">{subtitulo}</p>
        </div>
        <div class="brand-badge d-none d-sm-block"><i class="bi bi-hdd-network"></i> StockWeb</div>
    </div>

    <div class="card-form">
        <div class="card-form-title">Informações do Produto</div>
        <form action="/cadastro" method="POST">
            {id_hidden}
            <div class="row g-3">
                <div class="col-md-8 col-12">
                    <label class="form-label">Nome do Produto</label>
                    <input type="text" class="form-control" name="nome" value="{nome_val}" placeholder="Digite o nome do produto" required>
                </div>
                <div class="col-md-4 col-12">
                    <label class="form-label">Quantidade</label>
                    <input type="number" class="form-control" name="quantidade" value="{qtd_val}" placeholder="Digite a quantidade" required>
                </div>
                <div class="col-md-4 col-12">
                    <label class="form-label">Data de Validade</label>
                    <input type="date" class="form-control" name="data_validade" value="{data_val}" required>
                </div>
            </div>
            <div class="mt-4 pt-2">
                <button type="submit" class="btn btn-salvar px-4 me-md-2"><i class="bi bi-save me-1"></i> Salvar Produto</button>
                <a href="/cadastro" class="btn btn-limpar px-4"><i class="bi bi-eraser me-1"></i> Limpar Campos</a>
            </div>
        </form>
    </div>
    """
    return render_template_string(BASE_LAYOUT, content=cadastro_html, active_page="cadastro")

@app.route("/estoque")
def estoque():
    busca = request.args.get("busca", "")
    with get_db_connection() as conn:
        if busca:
            produtos_rows = conn.execute("SELECT * FROM produtos WHERE nome LIKE ? ORDER BY data_validade ASC", (f"%{busca}%",)).fetchall()
        else:
            produtos_rows = conn.execute("SELECT * FROM produtos ORDER BY data_validade ASC").fetchall()

    tabela_linhas = ""
    total_produtos = len(produtos_rows)

    for row in produtos_rows:
        dt = datetime.strptime(row["data_validade"], "%Y-%m-%d")
        data_formatada = dt.strftime("%d/%m/%Y")
        status = calcular_status(row["data_validade"])

        tabela_linhas += f"""
        <tr>
            <td>{row["nome"]}</td>
            <td>{row["quantidade"]}</td>
            <td>{data_formatada}</td>
            <td><span class="status-badge {status["classe"]}">{status["label"]}</span></td>
            <td>
                <a href="/cadastro?editar={row["id"]}" class="btn btn-action-edit"><i class="bi bi-pencil-fill"></i></a>
                <a href="/excluir/{row["id"]}" class="btn btn-action-delete" onclick="return confirm('Deseja realmente remover este item?')"><i class="bi bi-trash-fill"></i></a>
            </td>
        </tr>
        """

    if not tabela_linhas:
        tabela_linhas = '<tr><td colspan="5" class="text-center text-muted py-4">Nenhum produto cadastrado ou encontrado.</td></tr>'

    estoque_html = f"""
    <div class="d-flex justify-content-between align-items-start mb-4">
        <div>
            <h2 class="top-header-title m-0">Estoque de Produtos</h2>
            <p class="top-header-sub m-0">Visualize e gerencie todos os produtos cadastrados.</p>
        </div>
        <div class="brand-badge d-none d-sm-block"><i class="bi bi-hdd-network"></i> StockWeb</div>
    </div>

    <div class="row mb-3 g-2 justify-content-between align-items-center">
        <div class="col-md-3 col-12">
            <a href="/cadastro" class="btn btn-novo w-100 text-center"><i class="bi bi-plus-lg me-1"></i> Novo Produto</a>
        </div>
        <div class="col-md-4 col-12">
            <form method="GET" action="/estoque" class="input-group">
                <input type="text" class="form-control" name="busca" value="{busca}" placeholder="Buscar produto...">
                <button class="btn btn-light border border-start-0" type="submit" style="background: #fff; color: #666;"><i class="bi bi-search"></i></button>
            </form>
        </div>
    </div>

    <div class="table-responsive" style="width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch;">
        <table class="table">
            <thead>
                <tr>
                    <th>Nome do Produto</th>
                    <th>Quantidade</th>
                    <th>Data de Validade</th>
                    <th>Status</th>
                    <th>Ações</th>
                </tr>
            </thead>
            <tbody>
                {tabela_linhas}
            </tbody>
        </table>
    </div>
    <div class="text-muted small mt-2 fw-medium">Total de produtos: {total_produtos}</div>
    """
    return render_template_string(BASE_LAYOUT, content=estoque_html, active_page="estoque")

@app.route("/excluir/<int:id>")
def excluir(id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM produtos WHERE id = ?", (id,))
        conn.commit()
    return redirect(url_for("estoque"))

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
