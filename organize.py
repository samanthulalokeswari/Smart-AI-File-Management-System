import os
import shutil


def organize_files(files, workspace):
    results = []
    errors = []

    for item in files:

        source = item["Path"]
        category = item["Category"]

        destination_folder = os.path.join(
            workspace,
            category
        )

        try:

            os.makedirs(
                destination_folder,
                exist_ok=True
            )

            filename = item["Name"]

            destination = os.path.join(
                destination_folder,
                filename
            )

            if os.path.abspath(source) == os.path.abspath(destination):
                continue

            if os.path.exists(destination):

                base, extension = os.path.splitext(
                    filename
                )

                counter = 1

                while os.path.exists(destination):

                    new_name = f"{base}_{counter}{extension}"

                    destination = os.path.join(
                        destination_folder,
                        new_name
                    )

                    counter += 1

            shutil.move(
                source,
                destination
            )

            results.append({
                "Name": filename,
                "Category": category,
                "Destination": destination
            })

        except (PermissionError, OSError) as error:

            errors.append({
                "Name": item["Name"],
                "Error": str(error)
            })

    return results, errors