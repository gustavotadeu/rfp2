import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AIPrompt, listPrompts, deletePrompt } from '../../../api/aiPromptsApi'; // Adjusted path

const AIPromptListPage: React.FC = () => {
  const [prompts, setPrompts] = useState<AIPrompt[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchPrompts = async () => {
      try {
        setLoading(true);
        const data = await listPrompts();
        setPrompts(data);
        setError(null);
      } catch (err) {
        setError('Failed to fetch prompts. Please try again.');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchPrompts();
  }, []);

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this prompt?')) {
      try {
        await deletePrompt(id);
        setPrompts(prompts.filter(p => p.id !== id)); // Update UI
      } catch (err) {
        setError('Failed to delete prompt. It might be in use or another error occurred.');
        console.error(err);
      }
    }
  };

  if (loading) {
    return <div className="p-4">Loading prompts...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-500">{error}</div>;
  }

  return (
    <div className="p-6 bg-gray-100 min-h-screen">
      <div className="container mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-gray-800">AI Prompts Management</h1>
          <Link
            to="/admin/prompts/new"
            className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out"
          >
            Create New Prompt
          </Link>
        </div>

        {prompts.length === 0 ? (
          <p className="text-gray-600">No prompts found. Get started by creating a new one!</p>
        ) : (
          <div className="bg-white shadow-md rounded-lg overflow-hidden">
            <table className="min-w-full leading-normal">
              <thead>
                <tr className="bg-gray-200 text-gray-600 uppercase text-sm leading-normal">
                  <th className="py-3 px-6 text-left">Name</th>
                  <th className="py-3 px-6 text-left">Description</th>
                  <th className="py-3 px-6 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="text-gray-700 text-sm">
                {prompts.map(prompt => (
                  <tr key={prompt.id} className="border-b border-gray-200 hover:bg-gray-100">
                    <td className="py-4 px-6 text-left whitespace-nowrap">
                      <span className="font-semibold">{prompt.name}</span>
                    </td>
                    <td className="py-4 px-6 text-left">
                      {prompt.description ? (prompt.description.substring(0, 100) + (prompt.description.length > 100 ? '...' : '')) : 'N/A'}
                    </td>
                    <td className="py-4 px-6 text-center">
                      <button
                        onClick={() => navigate(`/admin/prompts/edit/${prompt.id}`)}
                        className="bg-yellow-500 hover:bg-yellow-600 text-white font-semibold py-1 px-3 rounded text-xs mr-2 transition duration-150 ease-in-out"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(prompt.id)}
                        className="bg-red-500 hover:bg-red-600 text-white font-semibold py-1 px-3 rounded text-xs transition duration-150 ease-in-out"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIPromptListPage;
