Finally we want to save our data. To do this simply run:

```python
data_hub.save_data()
```

That is the quickest way to save data. In this case it will save the outputs (that is the data, data flags, figures, pdf etc.) into a folder. By default this will create the folder in the current working directory, name it after the site name, and append a timestamp. The timestamp means that you can run several trials, perhaps with different steps, and you wont mix them up later!

There are additional options that can be applied here however:

```python
from pathlib.path import Path

data_hub.save_data(
    folder_name = "first_test",
    save_folder_location = Path("/path/to/save/location"),
    use_custom_column_names: bool = False,
    custom_column_names_dict: dict | None = None,
    append_timestamp: bool = True
) -> None

```