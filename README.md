# Cloud Storage Backups

### Invoke App

```
gsb -c path/to/config.ini --provider google --local-path /path/to/local/file --remote-path bucket/path --console-log-level debug
```

### Config File

config.ini

```
[google]
private_key_json_file=/path/to/json/file.json
bucket=my_bucket
```