from mockhaus.server.concurrent_session_manager import ConcurrentSessionManager, SessionContext


concurrent_session_manager = ConcurrentSessionManager()

def get_session_manager() -> ConcurrentSessionManager:
    return concurrent_session_manager
