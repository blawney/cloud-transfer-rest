class InitUpload(generics.CreateAPIView):

    def post(self, request, *args, **kwargs):
        data = request.data
        try:
            transfer_data = data['transfers']
        except KeyError as ex:
            raise exceptions.RequestError('The request JSON body did not contain the required "transfers" key')

        # need to add owner information if not contained in the payload data.
        # if a list was passed, check each element
        if isinstance(transfer_data, list):
            for item in transfer_data:
                try:
                    # if 'owner' was included in the object, check that the owner PK matches theirs
                    # unless the requet was issued by an admin
                    intended_owner = item['owner']
                    if (not request.user.is_staff) and (request.user.pk != intended_owner):
                        raise exceptions.RequestError('''
                            Cannot assign ownership to someone other than yourself.''')
                except KeyError as ex:
                    # if 'owner' key was missing, just add the primary key of the requester
                    item['owner'] = request.user.pk
        # if a dict was passed (single item to transfer), then check the owner key 
        elif isinstance(transfer_data, dict):
            try:
                # if 'owner' was included in the object, check that the owner PK matches theirs
                # unless the requet was issued by an admin
                intended_owner = transfer_data['owner']
                if (not request.user.is_staff) and (request.user.pk != intended_owner):
                    raise exceptions.RequestError('''
                        Cannot assign ownership to someone other than yourself.''')
            except KeyError as ex:
                transfer_data['owner'] = request.user.pk
        else:
            raise ParseError

        # instantiate an instance of ResourceList, which 
        # allows us to use the serializer for that API view.
        rl = ResourceList()
        serializer_cls = rl.get_serializer_class()
        kwargs['data'] = transfer_data
        kwargs['many'] = isinstance(transfer_data, list)
        kwargs['context'] = {'request': request, 'format': self.format_kwarg}
        serializer = serializer_cls(*args, **kwargs)

        try:
            resource_objs = create_resource(serializer, request.user)
            tc = TransferCoordinator()
            tc.save()
            destination = utils.get_or_create_upload_location(request.user)
            if isinstance(resource_objs, Resource):
                resource_objs = [resource_objs,]
            for resource in resource_objs:
                t = Transfer(
                     download=False,
                     resource=resource,
                     destination=destination,
                     coordinator=tc 
                )
                t.save()
 
            # actually do the transfers (asynchronously):
            transfer_tasks.perform_transfers.delay(tc.pk)
        except Exception as ex:
            return exception_handler(ex, None)

        return Response({'message': 'thanks'})
