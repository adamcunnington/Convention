import convention
import convention.views
import convention.auth.views
import convention.api.views
import convention.users.views
from convention import models


if __name__ == "__main__":
    models.db.create_all()
    convention.app.run(threaded=True)
