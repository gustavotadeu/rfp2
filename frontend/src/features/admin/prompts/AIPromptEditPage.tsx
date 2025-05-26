import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { AIPrompt, AIPromptCreateData, AIPromptUpdateData, getPrompt, createPrompt, updatePrompt } from '../../../api/aiPromptsApi'; // Adjusted path

const AIPromptEditPage: React.FC = () => {
  const { id } = useParams<{ id?: string }>(); // id is string or undefined
  const navigate = useNavigate();
  const isEditMode = Boolean(id);

  const [name, setName] = useState<string>('');
  const [description, setDescription] = useState<string>('');
  const [promptText, setPromptText] = useState<string>('');
  
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (isEditMode && id) {
      const fetchPromptData = async () => {
        setLoading(true);
        try {
          const promptData = await getPrompt(Number(id));
          setName(promptData.name);
          setDescription(promptData.description || '');
          setPromptText(promptData.prompt_text);
          setError(null);
        } catch (err) {
          setError('Failed to fetch prompt data. Please try again.');
          console.error(err);
        } finally {
          setLoading(false);
        }
      };
      fetchPromptData();
    }
  }, [id, isEditMode]);

  const validateForm = (): boolean => {
    if (!name.trim()) {
      setFormError('Name is required.');
      return false;
    }
    if (!promptText.trim()) {
      setFormError('Prompt Text is required.');
      return false;
    }
    setFormError(null);
    return true;
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setError(null);

    const promptData: AIPromptCreateData | AIPromptUpdateData = {
      name,
      description: description.trim() === '' ? null : description, // Send null if empty
      prompt_text: promptText,
    };

    try {
      if (isEditMode && id) {
        await updatePrompt(Number(id), promptData as AIPromptUpdateData);
      } else {
        await createPrompt(promptData as AIPromptCreateData);
      }
      navigate('/admin/prompts'); // Navigate back to list on success
    } catch (err: any) {
      const apiError = err.response?.data?.detail || 'An unexpected error occurred.';
      setError(`Failed to save prompt: ${apiError}`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && isEditMode && !name) { // Initial loading for edit mode
    return <div className="p-4">Loading prompt details...</div>;
  }
  
  if (error && !isEditMode && !name) { // Error fetching for edit mode
     return <div className="p-4 text-red-500">{error}</div>;
  }


  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <div className="container mx-auto max-w-2xl">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">
          {isEditMode ? 'Edit AI Prompt' : 'Create New AI Prompt'}
        </h1>

        {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">{error}</div>}
        {formError && <div className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded relative mb-4" role="alert">{formError}</div>}

        <form onSubmit={handleSubmit} className="bg-white shadow-md rounded-lg p-8">
          <div className="mb-6">
            <label htmlFor="name" className="block text-gray-700 text-sm font-bold mb-2">
              Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
          </div>

          <div className="mb-6">
            <label htmlFor="description" className="block text-gray-700 text-sm font-bold mb-2">
              Description
            </label>
            <textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            />
          </div>

          <div className="mb-6">
            <label htmlFor="promptText" className="block text-gray-700 text-sm font-bold mb-2">
              Prompt Text <span className="text-red-500">*</span>
            </label>
            <textarea
              id="promptText"
              value={promptText}
              onChange={(e) => setPromptText(e.target.value)}
              rows={15} // Increased rows for better UX
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm" // Monospaced font for prompts
              disabled={loading}
            />
          </div>

          <div className="flex items-center justify-end space-x-4">
            <button
              type="button"
              onClick={() => navigate('/admin/prompts')}
              className="bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out"
              disabled={loading}
            >
              {loading ? (isEditMode ? 'Saving...' : 'Creating...') : (isEditMode ? 'Save Changes' : 'Create Prompt')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AIPromptEditPage;
