class Session:
    _instance = None
    _employeeId = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Session, cls).__new__(cls)
        return cls._instance

    def setEmployeeId(self, employeeId: str):
        Session._employeeId = employeeId

    def getEmployeeId(self) -> str:
        return Session._employeeId
