import dropbox

access_token = 'sl.u.AFt5rWsv8-i5pQ3Bd9uPmD79ZjZe_G6hVGfYtvp6txOgNcd0CFeKYC4ejbY9y_OnNLQw2o21oles9es1mXjelRliGxZjj7BZJrvQLi2AKSm__NFpIV-9K1ZHp-Nh3Nw-qt-837c9_x7yIrK4W5xWWQ0XUmMr4SCzh_R2mqRTAtaupK8zAnYqudDndiwK-iJRBAH1jX0JBMNV21OI3p4A6IVYFBmQc_4ZT7e_4RS3-ZMCM28gtCkxBi6sgop_4HZs6bUJ4bGwge0id3J0I_9oNzBNqcn_8K8sd0NcHTIIV958nR6w81TlpF-Nj3I1D8WAJQkbMXcav6HIC28OJtfD_963sLDmzkiSTvgpYDaQzj5JuJynPL0-mRaXVChtAFF32r6eZu0vAmR-4f2wLZrK4ncaRo8d56OWWojSnVAG1_C4Xjv4UUJwnj7sTfkFK7g5aXc8Gs7hZKWb0Z2LdzOczL5eojmWPZ4tGpH79A3D4oIsXrmuyFNttbQfB3lRkChKUEJ1Wy__7dnYCDZ5wuIqFaQQqbdKBFXDHxuS5jDvilGJvDAVFUtR5L0coz-IK2ZJ_bTnQfHzdRQmnJa-LmpUj2inAX-eF0Dug6bQfP0lrJwlpq2QQexwQRhxTv57I88zvDYiIpgkunUpQEKRty_ho2uJPqCzM8nwwhWIIqeCs98SMmNiaIR5TCIZuNmer9GTw0fMI16LJEGxlyidsZHA-bbeMdk8U5xAdmvh_HCAZCFl1ssI7v87XJIOSJRrRqjViWr1I5tcRYfZX7yh-N_6m_5FVYtz0qMsa8sl7iwLzuCmzLRmR4f2ww3FS1KbWEC0J1K9abZp-hYXpWe_uqghmgdR2RU8tAZG4rdqMLdBnLqpatDUk5oduPLVqGrBUBmGVF4hUPlidxAUFRO3hYezDszQRRIEJYS7j53emUKPqSUuXGS54BgH4PdUDTvTGPy6VSNIlGboFrtwe57bumhJXn8REjckPb5vzXa_gXcwwMNTYMQE18hNqgXMBw6RcmW74wcXNfX4duWp3-qRxL9jIgIxSGkHebzJMQbRA64t4v3JjPlvsEpSEtvTV1tQWWQXOK4yj1pJJD_5sHfsJlWQQakuz-mE7gaxfBYepW1f4gge9h51AKDDtoJGssw1seBKdnPE9xC4cApJgW2cdFc4l1YYKelIITzQCSD-_0VMxQgogPOQkNPwjMwPZq3i1HBojukqtyum0nRoW6PvKbmj6WMTuoWfx5jhA2JazrI0XdDeX-RjduVmRel6o3d6DvwxZG3VV4dTnbGY-tTiflVGaDV5jJEdahSoehKVAisoZ1gngA'
dpx = dropbox.Dropbox(access_token)

def list_files_with_sizes(folder_path):
    try:
        response = dpx.files_list_folder(folder_path)
        files = response.entries
        while response.has_more:
            response = dpx.files_list_folder_continue(response.cursor)
            files.extend(response.entries)

        file_info = []
        for f in files:
            if isinstance(f, dropbox.files.FileMetadata):
                file_info.append((f.name, f.size))  # Name and size in bytes
        return file_info
    except dropbox.exceptions.ApiError as err:
        print(f"API error: {err}")
        return []

# Example usage
files = list_files_with_sizes('/logfiles')
for name, size in files:
    print(f"{name} — {size / 1024:.2f} KB")



def download_file(file_path, local_path):
    try:
        with open(local_path, "wb") as f:
            metadata, res = dpx.files_download(file_path)
            f.write(res.content)
        print(f"Downloaded {file_path} to {local_path}")
    except dropbox.exceptions.ApiError as err:
        print(f"API error: {err}")
    except Exception as e:
        print(f"Error downloading file: {e}")

