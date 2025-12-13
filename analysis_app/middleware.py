class DisableSessionForAPI:
    """
    특정 URL 경로(/start_distributed_rebuild/)에 대해
    SessionMiddleware가 동작하기 전에 request에서 세션 객체를 제거하여
    세션 저장을 근본적으로 차단합니다.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # 세션을 비활성화할 URL 경로 목록
        self.DISABLE_SESSION_URLS = [
            '/start_distributed_rebuild/',
            '/start_distributed_rebuild',
        ]

    def __call__(self, request):
        # 요청 URL이 세션 비활성화 목록에 있는지 확인
        if request.path_info in self.DISABLE_SESSION_URLS:
            # SessionMiddleware보다 먼저 세션 관련 객체를 제거
            if hasattr(request, 'session'):
                del request.session

            # (선택 사항: 사용자 인증도 필요 없다면)
            if hasattr(request, 'user'):
                request.user = None

        response = self.get_response(request)
        return response