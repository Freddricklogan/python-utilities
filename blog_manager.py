#!/usr/bin/env python3
"""
Blog Manager - Python Command Line Version
Features: Create, edit, publish posts, categories, tags, comments
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Set
import argparse
import sys
from dataclasses import dataclass, asdict, field
import uuid
import re
from pathlib import Path


@dataclass
class Comment:
    id: str
    author: str
    email: str
    content: str
    created_at: str
    approved: bool = False
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


@dataclass
class Post:
    id: str
    title: str
    content: str
    excerpt: str = ""
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    author: str = "Admin"
    created_at: str = ""
    updated_at: str = ""
    published: bool = False
    featured: bool = False
    views: int = 0
    comments: List[Comment] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if not self.excerpt and self.content:
            # Generate excerpt from content (first 200 characters)
            self.excerpt = self.content[:200] + "..." if len(self.content) > 200 else self.content
    
    def update(self):
        """Update the post's updated_at timestamp."""
        self.updated_at = datetime.now().isoformat()
    
    @property
    def slug(self) -> str:
        """Generate URL-friendly slug from title."""
        return re.sub(r'[^\w\s-]', '', self.title.lower()).strip().replace(' ', '-')
    
    @property
    def word_count(self) -> int:
        """Calculate word count of content."""
        return len(self.content.split())
    
    @property
    def read_time(self) -> int:
        """Estimate reading time in minutes (250 words per minute)."""
        return max(1, self.word_count // 250)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['comments'] = [asdict(comment) for comment in self.comments]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Post':
        """Create Post from dictionary."""
        data = data.copy()
        comments_data = data.pop('comments', [])
        post = cls(**data)
        post.comments = [Comment(**comment_data) for comment_data in comments_data]
        return post


class BlogManager:
    def __init__(self, data_dir: str = "blog_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.posts_file = self.data_dir / "posts.json"
        self.config_file = self.data_dir / "config.json"
        
        self.posts: List[Post] = []
        self.categories: Set[str] = {"general", "technology", "programming", "tutorials", "news"}
        self.load_data()
    
    def load_data(self):
        """Load posts and configuration."""
        # Load posts
        if self.posts_file.exists():
            try:
                with open(self.posts_file, 'r') as f:
                    posts_data = json.load(f)
                    self.posts = [Post.from_dict(post_data) for post_data in posts_data]
                print(f"📚 Loaded {len(self.posts)} posts")
            except Exception as e:
                print(f"❌ Error loading posts: {e}")
        
        # Load config
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.categories.update(config.get('categories', []))
            except Exception as e:
                print(f"❌ Error loading config: {e}")
    
    def save_data(self):
        """Save posts and configuration."""
        try:
            # Save posts
            with open(self.posts_file, 'w') as f:
                posts_data = [post.to_dict() for post in self.posts]
                json.dump(posts_data, f, indent=2)
            
            # Save config
            config = {
                'categories': list(self.categories),
                'last_updated': datetime.now().isoformat()
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"💾 Saved {len(self.posts)} posts")
        except Exception as e:
            print(f"❌ Error saving data: {e}")
    
    def create_post(self, title: str, content: str, category: str = "general", 
                   tags: List[str] = None, author: str = "Admin", 
                   publish: bool = False, featured: bool = False) -> Post:
        """Create a new blog post."""
        if tags is None:
            tags = []
        
        # Add category to known categories
        self.categories.add(category)
        
        post = Post(
            id="",  # Will be generated in __post_init__
            title=title,
            content=content,
            category=category,
            tags=tags,
            author=author,
            published=publish,
            featured=featured
        )
        
        self.posts.insert(0, post)  # Add to beginning
        self.save_data()
        
        status = "published" if publish else "draft"
        print(f"✅ Created {status} post: '{title}'")
        return post
    
    def edit_post(self, post_id: str, title: str = None, content: str = None,
                 category: str = None, tags: List[str] = None) -> bool:
        """Edit an existing post."""
        post = self.get_post_by_id(post_id)
        if not post:
            print(f"❌ Post with ID {post_id} not found")
            return False
        
        if title:
            post.title = title
        if content:
            post.content = content
            post.excerpt = content[:200] + "..." if len(content) > 200 else content
        if category:
            post.category = category
            self.categories.add(category)
        if tags is not None:
            post.tags = tags
        
        post.update()
        self.save_data()
        
        print(f"✅ Updated post: '{post.title}'")
        return True
    
    def publish_post(self, post_id: str) -> bool:
        """Publish a post."""
        post = self.get_post_by_id(post_id)
        if not post:
            print(f"❌ Post with ID {post_id} not found")
            return False
        
        post.published = True
        post.update()
        self.save_data()
        
        print(f"📢 Published post: '{post.title}'")
        return True
    
    def unpublish_post(self, post_id: str) -> bool:
        """Unpublish a post."""
        post = self.get_post_by_id(post_id)
        if not post:
            print(f"❌ Post with ID {post_id} not found")
            return False
        
        post.published = False
        post.update()
        self.save_data()
        
        print(f"📝 Unpublished post: '{post.title}'")
        return True
    
    def delete_post(self, post_id: str) -> bool:
        """Delete a post."""
        post = self.get_post_by_id(post_id)
        if not post:
            print(f"❌ Post with ID {post_id} not found")
            return False
        
        self.posts.remove(post)
        self.save_data()
        
        print(f"🗑️ Deleted post: '{post.title}'")
        return True
    
    def feature_post(self, post_id: str) -> bool:
        """Feature a post."""
        post = self.get_post_by_id(post_id)
        if not post:
            print(f"❌ Post with ID {post_id} not found")
            return False
        
        # Unfeature other posts first
        for p in self.posts:
            p.featured = False
        
        post.featured = True
        post.update()
        self.save_data()
        
        print(f"⭐ Featured post: '{post.title}'")
        return True
    
    def get_post_by_id(self, post_id: str) -> Optional[Post]:
        """Get post by ID."""
        return next((post for post in self.posts if post.id == post_id), None)
    
    def get_post_by_slug(self, slug: str) -> Optional[Post]:
        """Get post by slug."""
        return next((post for post in self.posts if post.slug == slug), None)
    
    def list_posts(self, published_only: bool = False, category: str = None,
                  tag: str = None, search: str = None, featured_only: bool = False) -> List[Post]:
        """List posts with optional filters."""
        filtered_posts = self.posts.copy()
        
        if published_only:
            filtered_posts = [p for p in filtered_posts if p.published]
        
        if featured_only:
            filtered_posts = [p for p in filtered_posts if p.featured]
        
        if category:
            filtered_posts = [p for p in filtered_posts if p.category == category]
        
        if tag:
            filtered_posts = [p for p in filtered_posts if tag in p.tags]
        
        if search:
            search_lower = search.lower()
            filtered_posts = [
                p for p in filtered_posts 
                if search_lower in p.title.lower() or search_lower in p.content.lower()
            ]
        
        return filtered_posts
    
    def display_posts(self, posts: List[Post], detailed: bool = False):
        """Display posts in formatted output."""
        if not posts:
            print("📝 No posts found.")
            return
        
        print(f"\n📚 Found {len(posts)} post(s):")
        print("=" * 80)
        
        for post in posts:
            status_icon = "📢" if post.published else "📝"
            featured_icon = "⭐" if post.featured else ""
            
            print(f"{status_icon}{featured_icon} [{post.id[:8]}] {post.title}")
            
            if detailed:
                print(f"   📂 Category: {post.category}")
                print(f"   🏷️  Tags: {', '.join(post.tags) if post.tags else 'None'}")
                print(f"   👤 Author: {post.author}")
                print(f"   📊 Stats: {post.word_count} words, {post.read_time} min read, {post.views} views")
                print(f"   💬 Comments: {len(post.comments)}")
                
                created = datetime.fromisoformat(post.created_at)
                updated = datetime.fromisoformat(post.updated_at)
                print(f"   🕒 Created: {created.strftime('%Y-%m-%d %H:%M')}")
                if post.updated_at != post.created_at:
                    print(f"   🔄 Updated: {updated.strftime('%Y-%m-%d %H:%M')}")
                
                print(f"   📄 Excerpt: {post.excerpt[:100]}...")
                print()
    
    def display_post_content(self, post_id: str):
        """Display full post content."""
        post = self.get_post_by_id(post_id)
        if not post:
            print(f"❌ Post with ID {post_id} not found")
            return
        
        # Increment view count
        post.views += 1
        self.save_data()
        
        print(f"\n📖 {post.title}")
        print("=" * len(post.title))
        print(f"👤 By {post.author} | 📂 {post.category} | 🕒 {datetime.fromisoformat(post.created_at).strftime('%Y-%m-%d')}")
        print(f"🏷️  Tags: {', '.join(post.tags) if post.tags else 'None'}")
        print(f"📊 {post.word_count} words | ⏱️ {post.read_time} min read | 👁️ {post.views} views")
        print()
        print(post.content)
        
        if post.comments:
            print(f"\n💬 Comments ({len(post.comments)}):")
            print("-" * 40)
            for comment in post.comments:
                created = datetime.fromisoformat(comment.created_at)
                approved = "✅" if comment.approved else "⏳"
                print(f"{approved} {comment.author} ({created.strftime('%Y-%m-%d %H:%M')}):")
                print(f"   {comment.content}")
                print()
    
    def add_comment(self, post_id: str, author: str, email: str, content: str) -> bool:
        """Add a comment to a post."""
        post = self.get_post_by_id(post_id)
        if not post:
            print(f"❌ Post with ID {post_id} not found")
            return False
        
        comment = Comment(
            id="",  # Will be generated
            author=author,
            email=email,
            content=content,
            created_at=""  # Will be generated
        )
        
        post.comments.append(comment)
        post.update()
        self.save_data()
        
        print(f"💬 Added comment from {author} to post: '{post.title}'")
        return True
    
    def approve_comment(self, post_id: str, comment_id: str) -> bool:
        """Approve a comment."""
        post = self.get_post_by_id(post_id)
        if not post:
            print(f"❌ Post with ID {post_id} not found")
            return False
        
        comment = next((c for c in post.comments if c.id == comment_id), None)
        if not comment:
            print(f"❌ Comment with ID {comment_id} not found")
            return False
        
        comment.approved = True
        post.update()
        self.save_data()
        
        print(f"✅ Approved comment from {comment.author}")
        return True
    
    def get_statistics(self) -> Dict:
        """Get blog statistics."""
        total_posts = len(self.posts)
        published_posts = len([p for p in self.posts if p.published])
        draft_posts = total_posts - published_posts
        featured_posts = len([p for p in self.posts if p.featured])
        total_comments = sum(len(p.comments) for p in self.posts)
        total_views = sum(p.views for p in self.posts)
        
        # Category counts
        category_counts = {}
        for category in self.categories:
            category_counts[category] = len([p for p in self.posts if p.category == category])
        
        # Tag counts
        all_tags = []
        for post in self.posts:
            all_tags.extend(post.tags)
        tag_counts = {}
        for tag in set(all_tags):
            tag_counts[tag] = all_tags.count(tag)
        
        return {
            'total_posts': total_posts,
            'published_posts': published_posts,
            'draft_posts': draft_posts,
            'featured_posts': featured_posts,
            'total_comments': total_comments,
            'total_views': total_views,
            'categories': category_counts,
            'popular_tags': dict(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def display_statistics(self):
        """Display blog statistics."""
        stats = self.get_statistics()
        
        print("\n📊 Blog Statistics:")
        print("=" * 40)
        print(f"📚 Total Posts: {stats['total_posts']}")
        print(f"📢 Published: {stats['published_posts']}")
        print(f"📝 Drafts: {stats['draft_posts']}")
        print(f"⭐ Featured: {stats['featured_posts']}")
        print(f"💬 Total Comments: {stats['total_comments']}")
        print(f"👁️ Total Views: {stats['total_views']}")
        
        print(f"\n📂 Posts by Category:")
        for category, count in stats['categories'].items():
            if count > 0:
                print(f"   {category}: {count}")
        
        if stats['popular_tags']:
            print(f"\n🏷️ Popular Tags:")
            for tag, count in list(stats['popular_tags'].items())[:5]:
                print(f"   {tag}: {count}")
    
    def export_posts(self, filename: str = None, format: str = "json") -> str:
        """Export posts to file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"blog_export_{timestamp}.{format}"
        
        if format == "json":
            export_data = {
                'posts': [post.to_dict() for post in self.posts],
                'categories': list(self.categories),
                'statistics': self.get_statistics(),
                'export_date': datetime.now().isoformat()
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
        
        elif format == "csv":
            import csv
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['ID', 'Title', 'Category', 'Author', 'Published', 'Created', 'Views', 'Comments'])
                
                for post in self.posts:
                    writer.writerow([
                        post.id, post.title, post.category, post.author,
                        post.published, post.created_at, post.views, len(post.comments)
                    ])
        
        print(f"📤 Exported {len(self.posts)} posts to {filename}")
        return filename


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(description="Blog Manager")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create post
    create_parser = subparsers.add_parser('create', help='Create a new post')
    create_parser.add_argument('title', help='Post title')
    create_parser.add_argument('-c', '--content', default='', help='Post content')
    create_parser.add_argument('--category', default='general', help='Post category')
    create_parser.add_argument('--tags', nargs='*', default=[], help='Post tags')
    create_parser.add_argument('--author', default='Admin', help='Post author')
    create_parser.add_argument('--publish', action='store_true', help='Publish immediately')
    create_parser.add_argument('--featured', action='store_true', help='Mark as featured')
    
    # Edit post
    edit_parser = subparsers.add_parser('edit', help='Edit a post')
    edit_parser.add_argument('id', help='Post ID')
    edit_parser.add_argument('--title', help='New title')
    edit_parser.add_argument('--content', help='New content')
    edit_parser.add_argument('--category', help='New category')
    edit_parser.add_argument('--tags', nargs='*', help='New tags')
    
    # List posts
    list_parser = subparsers.add_parser('list', help='List posts')
    list_parser.add_argument('--published', action='store_true', help='Show only published posts')
    list_parser.add_argument('--featured', action='store_true', help='Show only featured posts')
    list_parser.add_argument('--category', help='Filter by category')
    list_parser.add_argument('--tag', help='Filter by tag')
    list_parser.add_argument('--search', help='Search in title and content')
    list_parser.add_argument('--detailed', action='store_true', help='Show detailed information')
    
    # View post
    view_parser = subparsers.add_parser('view', help='View a post')
    view_parser.add_argument('id', help='Post ID')
    
    # Publish/unpublish
    publish_parser = subparsers.add_parser('publish', help='Publish a post')
    publish_parser.add_argument('id', help='Post ID')
    
    unpublish_parser = subparsers.add_parser('unpublish', help='Unpublish a post')
    unpublish_parser.add_argument('id', help='Post ID')
    
    # Feature post
    feature_parser = subparsers.add_parser('feature', help='Feature a post')
    feature_parser.add_argument('id', help='Post ID')
    
    # Delete post
    delete_parser = subparsers.add_parser('delete', help='Delete a post')
    delete_parser.add_argument('id', help='Post ID')
    
    # Add comment
    comment_parser = subparsers.add_parser('comment', help='Add a comment')
    comment_parser.add_argument('post_id', help='Post ID')
    comment_parser.add_argument('author', help='Comment author')
    comment_parser.add_argument('email', help='Author email')
    comment_parser.add_argument('content', help='Comment content')
    
    # Statistics
    subparsers.add_parser('stats', help='Show blog statistics')
    
    # Export
    export_parser = subparsers.add_parser('export', help='Export posts')
    export_parser.add_argument('-f', '--file', help='Export filename')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='Export format')
    
    return parser


def main():
    """Main application entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    blog = BlogManager()
    
    try:
        if args.command == 'create':
            blog.create_post(
                args.title, args.content, args.category,
                args.tags, args.author, args.publish, args.featured
            )
        
        elif args.command == 'edit':
            blog.edit_post(args.id, args.title, args.content, args.category, args.tags)
        
        elif args.command == 'list':
            posts = blog.list_posts(
                args.published, args.category, args.tag, args.search, args.featured
            )
            blog.display_posts(posts, args.detailed)
        
        elif args.command == 'view':
            blog.display_post_content(args.id)
        
        elif args.command == 'publish':
            blog.publish_post(args.id)
        
        elif args.command == 'unpublish':
            blog.unpublish_post(args.id)
        
        elif args.command == 'feature':
            blog.feature_post(args.id)
        
        elif args.command == 'delete':
            blog.delete_post(args.id)
        
        elif args.command == 'comment':
            blog.add_comment(args.post_id, args.author, args.email, args.content)
        
        elif args.command == 'stats':
            blog.display_statistics()
        
        elif args.command == 'export':
            blog.export_posts(args.file, args.format)
    
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()