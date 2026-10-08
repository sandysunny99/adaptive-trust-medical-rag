content = open('.github/workflows/ci.yml').read()
content = content.replace('''
    env:
      DATABASE_URL: "postgresql+asyncpg://u:p@localhost/db"
      PYTHONPATH: "src"
      GITHUB_ACTIONS: "true"''', '''
    env:
      DATABASE_URL: "postgresql+asyncpg://u:p@localhost/db"
      PYTHONPATH: "src"
      GITHUB_ACTIONS: "true"
      TESTING: "1"''')
open('.github/workflows/ci.yml', 'w').write(content)
