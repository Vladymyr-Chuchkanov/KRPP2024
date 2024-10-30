## Local development

### Run the server

1. Install python on your system
2. Move to the root directory of the project and create python virtual environment
    ```bash
    python -m venv venv
    ```
3. Activate the virtual environment
    ```bash
    source venv/bin/activate
    ```
4. Install the required python packages
    ```bash
    pip install -r requirements.txt
    ```
5. Run the server
    ```bash
    python app.py
    ```

6. (Optional) There is a simple client that can be opened on `http://localhost:5000` to interact with the server.
   Just open the link in your browser and try to send some messages. They should appear in the terminal where the server
   is running.
