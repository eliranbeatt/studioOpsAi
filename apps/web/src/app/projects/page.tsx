'use client'

import { useState } from 'react';
import { useProjects, Project } from '@/hooks/useProjects';
import ProjectForm from '@/components/ProjectForm';

export default function ProjectsPage() {
  const { projects, loading, error, createProject, deleteProject } = useProjects();
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  const handleCreateProject = async (data: Partial<Project>) => {
    try {
      await createProject(data);
      setShowCreateForm(false);
    } catch (error) {
      // Error is handled by the hook
    }
  };

  const handleDeleteProject = async (projectId: string) => {
    if (confirm('האם אתה בטוח שברצונך למחוק פרויקט זה?')) {
      try {
        await deleteProject(projectId);
      } catch (error) {
        // Error is handled by the hook
      }
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('he-IL');
  };

  const formatCurrency = (amount?: number) => {
    if (!amount) return '₪0';
    return `₪${amount.toLocaleString('he-IL')}`;
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-foreground">ניהול פרויקטים</h2>
            <p className="text-muted-foreground mt-1">
              צפה וניהול כל הפרויקטים שלך במקום אחד
            </p>
          </div>
          <button 
            className="btn btn-primary px-4 gradient-bg border-0 opacity-50"
            disabled
          >
            ➕ פרויקט חדש
          </button>
        </div>
        
        <div className="card border-border/50 bg-gradient-to-br from-card to-card/80 backdrop-blur-sm">
          <div className="text-center py-16">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">טוען פרויקטים...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-foreground">ניהול פרויקטים</h2>
            <p className="text-muted-foreground mt-1">
              צפה וניהול כל הפרויקטים שלך במקום אחד
            </p>
          </div>
          <button 
            className="btn btn-primary px-4 gradient-bg border-0"
            onClick={() => setShowCreateForm(true)}
          >
            ➕ פרויקט חדש
          </button>
        </div>
        
        <div className="card border-border/50 bg-gradient-to-br from-card to-card/80 backdrop-blur-sm">
          <div className="text-center text-red-500 py-16">
            <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <span className="text-red-500 text-3xl">⚠️</span>
            </div>
            <p className="text-lg font-light mb-2">שגיאה בטעינת פרויקטים</p>
            <p className="text-sm">{error.message}</p>
            <button 
              className="mt-4 btn btn-primary px-6 gradient-bg border-0"
              onClick={() => window.location.reload()}
            >
              נסה שוב
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground">ניהול פרויקטים</h2>
          <p className="text-muted-foreground mt-1">
            {projects.length} פרויקטים
          </p>
        </div>
        <button 
          className="btn btn-primary px-4 gradient-bg border-0"
          onClick={() => setShowCreateForm(true)}
        >
          ➕ פרויקט חדש
        </button>
      </div>

      {/* Projects List */}
      {projects.length === 0 ? (
        <div className="card border-border/50 bg-gradient-to-br from-card to-card/80 backdrop-blur-sm">
          <div className="text-center text-muted-foreground/70 py-16">
            <div className="w-20 h-20 bg-muted/50 rounded-full flex items-center justify-center mx-auto mb-6 backdrop-blur-sm">
              <span className="text-muted-foreground/40 text-3xl">📋</span>
            </div>
            <p className="text-lg font-light mb-2">אין פרויקטים להצגה</p>
            <p className="text-sm">התחל פרויקט חדש כדי לראות אותו כאן</p>
            <button 
              className="mt-4 btn btn-primary px-6 gradient-bg border-0"
              onClick={() => setShowCreateForm(true)}
            >
              צור פרויקט חדש
            </button>
          </div>
        </div>
      ) : (
        <div className="grid gap-4">
          {projects.map((project) => (
            <div key={project.id} className="card border-border/50 bg-gradient-to-br from-card to-card/80 backdrop-blur-sm p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-foreground mb-2">
                    {project.name}
                  </h3>
                  {project.client_name && (
                    <p className="text-muted-foreground mb-2">
                      לקוח: {project.client_name}
                    </p>
                  )}
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span className="badge badge-secondary">
                      {project.status}
                    </span>
                    {project.start_date && (
                      <span>התחלה: {formatDate(project.start_date)}</span>
                    )}
                    {project.due_date && (
                      <span>סיום: {formatDate(project.due_date)}</span>
                    )}
                    {project.budget_planned && (
                      <span>תקציב: {formatCurrency(project.budget_planned)}</span>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <button 
                    className="btn btn-ghost btn-sm"
                    onClick={() => setSelectedProject(project)}
                  >
                    ערוך
                  </button>
                  <button 
                    className="btn btn-ghost btn-sm text-red-500"
                    onClick={() => handleDeleteProject(project.id)}
                  >
                    מחק
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modals */}
      {showCreateForm && (
        <ProjectForm
          onSubmit={handleCreateProject}
          onCancel={() => setShowCreateForm(false)}
        />
      )}

      {selectedProject && (
        <ProjectForm
          project={selectedProject}
          onSubmit={async (data) => {
            // TODO: Implement update
            console.log('Update project:', selectedProject.id, data);
            setSelectedProject(null);
          }}
          onCancel={() => setSelectedProject(null)}
        />
      )}
    </div>
  )
}