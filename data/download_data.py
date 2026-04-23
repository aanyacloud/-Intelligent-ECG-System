import wfdb

print("Downloading MIT-BIH dataset...")
wfdb.dl_database("mitdb", dl_dir="data")
print("Download complete!")