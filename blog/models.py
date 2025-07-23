from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from ckeditor.fields import RichTextField

User = get_user_model()

class BlogCategory(models.Model):
    name = models.CharField(max_length=100, verbose_name=_('Nom'))
    slug = models.SlugField(unique=True, verbose_name=_('Slug'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    is_active = models.BooleanField(default=True, verbose_name=_('Actif'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Catégorie de blog')
        verbose_name_plural = _('Catégories de blog')
        ordering = ['name']
    
    def __str__(self):
        return self.name

class BlogPost(models.Model):
    STATUS_CHOICES = [
        ('draft', _('Brouillon')),
        ('published', _('Publié')),
        ('archived', _('Archivé')),
    ]
    
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts', limit_choices_to={'user_type': 'seller'})
    title = models.CharField(max_length=200, verbose_name=_('Titre'))
    slug = models.SlugField(unique=True, verbose_name=_('Slug'))
    excerpt = models.TextField(max_length=300, verbose_name=_('Extrait'))
    content = RichTextField(verbose_name=_('Contenu'))
    featured_image = models.ImageField(upload_to='blog_images/', verbose_name=_('Image à la une'))
    category = models.ForeignKey(BlogCategory, on_delete=models.CASCADE, related_name='posts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    views = models.IntegerField(default=0, verbose_name=_('Vues'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Article de blog')
        verbose_name_plural = _('Articles de blog')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})
    
    @property
    def is_published(self):
        return self.status == 'published'

class BlogComment(models.Model):
    post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(verbose_name=_('Commentaire'))
    is_approved = models.BooleanField(default=True, verbose_name=_('Approuvé'))
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('Commentaire de blog')
        verbose_name_plural = _('Commentaires de blog')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Commentaire de {self.author.username} sur {self.post.title}"