$env:OLLAMA_MODELS = 'D:\ollama\models'
$env:OLLAMA_CONTEXT_LENGTH = '65536'
$log = 'D:\hust-master\Thesis\report\2026-11-03\data\ollama'
$p = Start-Process -FilePath 'C:\Users\qdcon\AppData\Local\Programs\Ollama\ollama.exe' -ArgumentList 'serve' `
  -WindowStyle Hidden -RedirectStandardError "$log\server.log" -RedirectStandardOutput "$log\server.out.log" -PassThru
$p.Id
