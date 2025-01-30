from django.db.models import Exists, OuterRef
from rest_framework.permissions import IsAuthenticated
from rest_framework.validators import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from soccerapp.models import Team, Comment
from soccerapp.serializers import CommentSerializer

# views to list all of the comments of the specific team 
class CommentList(generics.ListCreateAPIView): 
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer

    # validate if the request has the required query param and return the value 
    def validate_query_param(self, request): 
        if request.query_params.get('team') is None: raise ValidationError("Team not defined.")
        return request.query_params.get("team")

    # get queryset
    def get_queryset(self):
        queried_team = Team.objects.get(pk=self.validate_query_param(self.request))

        # depending on 'reply_to', query the appropriate list of comments
        if self.request.query_params.get('reply_to') is None: 
            comment_list = Comment.objects.filter(team=queried_team, replyToComment__isnull=True)
        else: 
            parent_comment = get_object_or_404(Comment, pk=self.request.query_params.get('reply_to'))
            comment_list = Comment.objects.filter(team=queried_team, replyToComment=parent_comment)

        # annotate to add extra fields "is_liked_by_user" and "is_from_user"
        annotated_comment_list = comment_list.annotate(
            # check whether the specified queryset of likes from each comment exists
            # TODO: what is through keyword
            is_liked_by_user=Exists(Comment.likes.through.objects.filter(
                comment_id=OuterRef("pk"), 
                user=self.request.user
            )), 
            is_from_user=Exists(Comment.objects.filter(pk=OuterRef("pk"), user=self.request.user))
        )
        return annotated_comment_list
    
    def create(self, request, *args, **kwargs) -> Response: 
        request_data = request.data 
        request_data["user"] = request.user.pk
        request_data["team"] = self.validate_query_param(request)

        new_comment_serializer = self.get_serializer(data=request_data)
        new_comment_serializer.is_valid(raise_exception=True) # automatically raise the exception

        # the newly added comment
        created_comment = new_comment_serializer.save()

        # extra fields of the comment 
        created_comment.is_liked_by_user = False # the newly added comment must have no likes
        created_comment.is_from_user = True # the newly added comment must be from user

        # return the response with the list 
        return Response(self.get_serializer(created_comment).data, status=status.HTTP_201_CREATED)


# views to update the comment
class CommentDetail(generics.RetrieveUpdateDestroyAPIView): 
    permission_classes = [IsAuthenticated]
    serializer_class = CommentSerializer
    
    # overriding to make sure the object will always have extra fields 
    def get_object(self):
        queried_comment = get_object_or_404(Comment, pk=self.kwargs["pk"]) 

        # always add extra field of the instance 
        queried_comment.is_liked_by_user = (self.request.user in queried_comment.likes.all())
        queried_comment.is_from_user = (queried_comment.user == self.request.user)

        return queried_comment
    
    # override the update actiong the we only update content so we will update partially
    def update(self, request, *args, **kwargs): 
        kwargs["partial"] = True
        return super().update(request, *args, **kwargs)
    

# views to like the comment 
class LikeComment(APIView): 
    permission_classes = [IsAuthenticated]

    def post(self, request, pk: int, format=None) -> Response: 
        # query the comment 
        queried_comment = get_object_or_404(Comment, pk=pk)

        # if the user already likes the comment, then remove the user from list of likes 
        if request.user in queried_comment.likes.all(): 
            queried_comment.likes.remove(request.user)
        else: # otherwise, add the user to the list 
            queried_comment.likes.add(request.user)

        # extra fields 
        queried_comment.is_liked_by_user = (request.user in queried_comment.likes.all())
        queried_comment.is_from_user = (queried_comment.user == request.user)

        # serialize and return
        comment_serializer = CommentSerializer(queried_comment)
        return Response(comment_serializer.data)

