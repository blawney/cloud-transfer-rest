class ResourceListOrig(generics.ListCreateAPIView):
    '''
    This endpoint allows us to list or create Resources
    See methods below regarding listing logic and creation logic
    Some filtering can be added at some point
    '''
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('is_active',)
    

    def get_queryset(self):
        '''
        This overrides the get_queryset method of rest_framework.generics.GenericAPIView
        This allows us to return only Resource instances belonging to the user.
        If an admin is requesting, then we return all
        '''
        queryset = super(ResourceList, self).get_queryset()
        return filter_for_user(queryset, self.request.user)

    def create(self, request, *args, **kwargs):
        '''
        This override provides us with the ability to create multiple instances
        Pretty much a verbatim copy of the implementation from CreateMixin except
        that we add the many=... kwarg when we call get_serializer
        '''
        serializer = self.get_serializer(data=request.data, many=isinstance(request.data,list))
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        '''
        Override of rest_framework.mixins.CreateModelMixin.perform_create
        Allows admin users to create Resources for anyone.
        Allows non-admin users to create Resources only for themselves
        '''
        user = self.request.user

        # if the user is NOT staff, we only let them
        # create a Resource for themself.
        if not user.is_staff:
            try:
                if serializer.validated_data['owner'] == user:
                    serializer.save(owner=user)
                # here we block any effort to create a Resource for anyone else.
                #Raise 404 so we do not give anything away
                else:
                    raise Http404
            except KeyError as ex:
                serializer.save(owner=user)

        # Otherwsie (if the user IS staff), we trust them to create
        # Resources for themselves or others.
        else:
            serializer.save()
