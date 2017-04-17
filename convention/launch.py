import convention
import convention.views
import convention.api.views
from convention import models


if __name__ == "__main__":
    models.db.create_all()
    convention.app.run(debug=True)
